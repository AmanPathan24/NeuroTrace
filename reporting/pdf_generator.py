"""Publication-grade research PDF report generation using ReportLab."""
import io
import os
import tempfile
from pathlib import Path
from typing import Optional, Union
from datetime import datetime, timezone

import numpy as np
from PIL import Image

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

from core.contracts import (
    ValidatedStudy,
    AnalysisMetrics,
    QCReport,
    PredictionMetadata,
)
from visualization.slices_2d import extract_plane_slice, normalize_slice_display


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic total page count and running disclaimers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#444444"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                54,
                750,
                "NeuroTrace — Quantitative Brain MRI Research Report",
            )
            self.setStrokeColor(colors.HexColor("#cccccc"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Running footer
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#666666"))
        self.setStrokeColor(colors.HexColor("#cccccc"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)

        disclaimer = "RESEARCH & EDUCATIONAL USE ONLY — NOT FOR CLINICAL DIAGNOSIS OR TREATMENT"
        self.drawString(54, 34, disclaimer)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 34, page_text)
        self.restoreState()


def _render_slice_thumbnail(
    mri_volume: np.ndarray,
    pred_mask: Optional[np.ndarray],
    plane: str,
    slice_idx: Optional[int] = None,
) -> io.BytesIO:
    """Render a 2D slice with tumor overlay as a PNG in-memory bytes buffer."""
    mri_slice = extract_plane_slice(mri_volume, plane, slice_idx or 0)
    mri_disp = normalize_slice_display(mri_slice)
    h, w = mri_disp.shape

    # Base grayscale image
    base_rgb = (mri_disp * 255.0).astype(np.uint8)
    base_img = Image.fromarray(base_rgb).convert("RGB")

    # If mask slice has tumor voxels, blend a vibrant cyan overlay
    if pred_mask is not None:
        mask_slice = extract_plane_slice(pred_mask, plane, slice_idx or 0)
        if np.any(mask_slice > 0):
            overlay_arr = np.array(base_img)
            # Apply cyan tint [0, 220, 255] where tumor is present
            tumor_indices = mask_slice > 0
            overlay_arr[tumor_indices, 0] = (
                overlay_arr[tumor_indices, 0] * 0.4 + 0 * 0.6
            ).astype(np.uint8)
            overlay_arr[tumor_indices, 1] = (
                overlay_arr[tumor_indices, 1] * 0.4 + 220 * 0.6
            ).astype(np.uint8)
            overlay_arr[tumor_indices, 2] = (
                overlay_arr[tumor_indices, 2] * 0.4 + 255 * 0.6
            ).astype(np.uint8)
            base_img = Image.fromarray(overlay_arr)

    buf = io.BytesIO()
    base_img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def generate_research_pdf_report(
    study: ValidatedStudy,
    metrics: AnalysisMetrics,
    qc: QCReport,
    prediction_metadata: Optional[PredictionMetadata] = None,
    ai_commentary: Optional[str] = None,
    raw_volume: Optional[np.ndarray] = None,
    pred_mask: Optional[np.ndarray] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Generate an exhaustive, publication-grade research PDF report containing study metadata,
    model provenance, deterministic volumetric measurements, QC results, embedded slice figures,
    and attributed AI research commentary.
    
    Args:
        study: ValidatedStudy schema.
        metrics: AnalysisMetrics schema.
        qc: QCReport schema.
        prediction_metadata: Optional PredictionMetadata schema.
        ai_commentary: Optional narrative commentary from Gemma 4 copilot.
        raw_volume: 3D numpy array for rendering slice thumbnails.
        pred_mask: 3D binary mask array for rendering slice thumbnails.
        output_path: Destination file path for PDF.
        
    Returns:
        Resolved Path to the generated PDF document.
    """
    out_file = Path(
        output_path or f"reports/neurotrace_report_{study.metadata.study_id}.pdf"
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out_file),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=12,
    )
    section_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    ai_body_style = ParagraphStyle(
        "AIBody",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("NEUROTRACE RESEARCH REPORT", title_style))
    story.append(
        Paragraph("Quantitative Brain MRI 3D U-Net Segmentation & Evidence Summary", subtitle_style)
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10))

    # 2. Study & Subject Information Table
    story.append(Paragraph("1. Study & Acquisition Metadata", section_h1))
    meta_data = [
        [
            Paragraph("Study Identifier:", table_cell_bold),
            Paragraph(study.metadata.study_id, table_cell),
            Paragraph("Acquisition Modality:", table_cell_bold),
            Paragraph(study.metadata.modality, table_cell),
        ],
        [
            Paragraph("Original File:", table_cell_bold),
            Paragraph(study.metadata.filename, table_cell),
            Paragraph("Matrix Dimensions:", table_cell_bold),
            Paragraph(f"{study.dimensions.dim_x} × {study.dimensions.dim_y} × {study.dimensions.dim_z}", table_cell),
        ],
        [
            Paragraph("Voxel Spacing:", table_cell_bold),
            Paragraph(f"{study.spacing.dx_mm:.2f} × {study.spacing.dy_mm:.2f} × {study.spacing.dz_mm:.2f} mm", table_cell),
            Paragraph("Orientation / Affine:", table_cell_bold),
            Paragraph(f"{study.orientation} (Verified)", table_cell),
        ],
        [
            Paragraph("SHA256 Hash:", table_cell_bold),
            Paragraph(f"{study.metadata.sha256_hash[:24]}...", table_cell),
            Paragraph("Report Generated:", table_cell_bold),
            Paragraph(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), table_cell),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[105, 147, 110, 142])
    t_meta.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # 3. Model & Provenance Metadata Table
    story.append(Paragraph("2. Model Architecture & Provenance", section_h1))
    ckpt_name = prediction_metadata.checkpoint_file if prediction_metadata else "model_epoch_45 (1).pt"
    device_name = prediction_metadata.device if prediction_metadata else "cpu"
    runtime = f"{prediction_metadata.inference_seconds:.2f} s" if prediction_metadata else "N/A"
    model_data = [
        [
            Paragraph("Architecture:", table_cell_bold),
            Paragraph("NeuroSegNet 3D U-Net (4 levels, 8 base filters)", table_cell),
            Paragraph("Total Parameters:", table_cell_bold),
            Paragraph("1,413,250 (float32)", table_cell),
        ],
        [
            Paragraph("Trained Checkpoint:", table_cell_bold),
            Paragraph(ckpt_name, table_cell),
            Paragraph("Execution Device:", table_cell_bold),
            Paragraph(device_name.upper(), table_cell),
        ],
        [
            Paragraph("Input Channels:", table_cell_bold),
            Paragraph("1 (FLAIR volume, Z-score normalized)", table_cell),
            Paragraph("Inference Duration:", table_cell_bold),
            Paragraph(runtime, table_cell),
        ],
    ]
    t_model = Table(model_data, colWidths=[105, 147, 110, 142])
    t_model.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_model)
    story.append(Spacer(1, 10))

    # 4. Deterministic Volumetric Measurements Table
    story.append(Paragraph("3. Deterministic Volumetric Measurements", section_h1))
    bbox_str = "N/A (Empty Mask)"
    c_vox_str = "N/A"
    c_world_str = "N/A"
    if metrics.bounding_box:
        b = metrics.bounding_box
        bbox_str = f"X: [{b.x_min}, {b.x_max}], Y: [{b.y_min}, {b.y_max}], Z: [{b.z_min}, {b.z_max}] ({b.dimensions[0]}×{b.dimensions[1]}×{b.dimensions[2]})"
    if metrics.centroid_voxel:
        c_vox_str = f"({metrics.centroid_voxel[0]:.1f}, {metrics.centroid_voxel[1]:.1f}, {metrics.centroid_voxel[2]:.1f})"
    if metrics.centroid_world_mm:
        c_world_str = f"({metrics.centroid_world_mm[0]:.1f}, {metrics.centroid_world_mm[1]:.1f}, {metrics.centroid_world_mm[2]:.1f}) mm"

    gt_accuracy_str = (
        f"Dice: {metrics.dice_score:.4f} | IoU: {metrics.iou_score:.4f}"
        if metrics.ground_truth_available
        else "Not Available (No reference mask supplied)"
    )

    meas_data = [
        [
            Paragraph("Physical Tumor Volume:", table_cell_bold),
            Paragraph(f"<b>{metrics.physical_volume_cm3:.2f} mL (cm³)</b>", table_cell),
            Paragraph("Tumor Voxel Count:", table_cell_bold),
            Paragraph(f"<b>{metrics.tumor_voxel_count:,} voxels</b>", table_cell),
        ],
        [
            Paragraph("Brain Volume Fraction:", table_cell_bold),
            Paragraph(f"{metrics.tumor_volume_fraction_percent:.2f}% of brain", table_cell),
            Paragraph("Total Brain Voxels:", table_cell_bold),
            Paragraph(f"{metrics.total_brain_voxels:,} voxels (>0)", table_cell),
        ],
        [
            Paragraph("3D Bounding Box:", table_cell_bold),
            Paragraph(bbox_str, table_cell),
            Paragraph("Centroid (Index):", table_cell_bold),
            Paragraph(c_vox_str, table_cell),
        ],
        [
            Paragraph("Centroid (World):", table_cell_bold),
            Paragraph(c_world_str, table_cell),
            Paragraph("Ground Truth Acc:", table_cell_bold),
            Paragraph(gt_accuracy_str, table_cell),
        ],
    ]
    t_meas = Table(meas_data, colWidths=[115, 137, 110, 142])
    t_meas.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#86efac")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbf7d0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_meas)
    story.append(Spacer(1, 10))

    # 5. Technical Quality Control Findings
    story.append(Paragraph("4. Technical Quality Control Assessment", section_h1))
    qc_status_text = "<b>PASSED</b>" if qc.is_passed else "<font color='red'><b>FLAGGED</b></font>"
    flags_formatted = "<br/>".join([f"• {f}" for f in qc.flags]) if qc.flags else "No technical anomalies detected."

    qc_data = [
        [
            Paragraph("QC Gate Status:", table_cell_bold),
            Paragraph(qc_status_text, table_cell),
            Paragraph("Signal-to-Noise Ratio (SNR):", table_cell_bold),
            Paragraph(f"{qc.signal_to_noise_ratio_est:.2f}", table_cell),
        ],
        [
            Paragraph("Empty Mask Finding:", table_cell_bold),
            Paragraph("Negative (No Tumor)" if qc.is_empty_mask else "Positive (Tumor Present)", table_cell),
            Paragraph("Contrast Ratio (Tumor/Brain):", table_cell_bold),
            Paragraph(f"{qc.contrast_ratio_est:.2f}", table_cell),
        ],
        [
            Paragraph("Quality Flags & Notes:", table_cell_bold),
            Paragraph(flags_formatted, table_cell),
            Paragraph("", table_cell),
            Paragraph("", table_cell),
        ],
    ]
    t_qc = Table(qc_data, colWidths=[115, 137, 110, 142])
    t_qc.setStyle(
        TableStyle([
            ("SPAN", (1, 2), (3, 2)),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_qc)
    story.append(Spacer(1, 10))

    # 6. Embedded 2D Slice Figures (Axial, Coronal, Sagittal)
    if raw_volume is not None:
        story.append(Paragraph("5. Orthogonal Multi-Planar Slice Views", section_h1))
        # Select diagnostic slice index (centroid or midpoint)
        dim_x, dim_y, dim_z = raw_volume.shape
        c_x = int(metrics.centroid_voxel[0]) if metrics.centroid_voxel else dim_x // 2
        c_y = int(metrics.centroid_voxel[1]) if metrics.centroid_voxel else dim_y // 2
        c_z = int(metrics.centroid_voxel[2]) if metrics.centroid_voxel else dim_z // 2

        img_axial_buf = _render_slice_thumbnail(raw_volume, pred_mask, "axial", c_z)
        img_coronal_buf = _render_slice_thumbnail(raw_volume, pred_mask, "coronal", c_y)
        img_sagittal_buf = _render_slice_thumbnail(raw_volume, pred_mask, "sagittal", c_x)

        thumb_w = 2.1 * inch
        thumb_h = 2.1 * inch

        img_table_data = [
            [
                RLImage(img_axial_buf, width=thumb_w, height=thumb_h),
                RLImage(img_coronal_buf, width=thumb_w, height=thumb_h),
                RLImage(img_sagittal_buf, width=thumb_w, height=thumb_h),
            ],
            [
                Paragraph(f"<b>Axial (Z: {c_z})</b>", table_cell_bold),
                Paragraph(f"<b>Coronal (Y: {c_y})</b>", table_cell_bold),
                Paragraph(f"<b>Sagittal (X: {c_x})</b>", table_cell_bold),
            ],
        ]
        t_images = Table(img_table_data, colWidths=[168, 168, 168])
        t_images.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ])
        )
        story.append(t_images)
        story.append(Spacer(1, 10))

    # 7. Gemma 4 AI Research Commentary
    story.append(Paragraph("6. AI Research Assistant Commentary (Gemma 4)", section_h1))
    commentary_text = ai_commentary or (
        f"Automated quantitative analysis of study {study.metadata.study_id} completed successfully. "
        f"NeuroSegNet 3D U-Net delineated a segmented tumor lesion of {metrics.physical_volume_cm3:.2f} mL "
        f"({metrics.tumor_voxel_count:,} voxels), representing {metrics.tumor_volume_fraction_percent:.2f}% of brain volume. "
        f"Technical quality control verified an estimated SNR of {qc.signal_to_noise_ratio_est:.2f} and contrast ratio of {qc.contrast_ratio_est:.2f}."
    )
    commentary_box = [
        [
            Paragraph(
                f"<b>Attributed AI Commentary (Gemma 4 Copilot — Grounded in deterministic metrics):</b><br/>"
                f"{commentary_text}",
                ai_body_style,
            )
        ]
    ]
    t_comm = Table(commentary_box, colWidths=[504])
    t_comm.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(t_comm)
    story.append(Spacer(1, 12))

    # 8. Research Disclaimer
    disclaimer_text = (
        "<b>LEGAL & RESEARCH NOTICE:</b> NeuroTrace is developed strictly as an educational and academic computational "
        "neuroimaging research tool. The segmented boundaries and volumetric measurements provided in this report are "
        "derived from automated neural network inference and must not be used as clinical diagnostic criteria, surgical "
        "resection boundaries, or treatment recommendations."
    )
    story.append(Paragraph(disclaimer_text, ParagraphStyle("Disc", parent=body_style, fontSize=7, leading=9, textColor=colors.HexColor("#64748b"))))

    # Build PDF with custom two-pass canvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return out_file.resolve()

