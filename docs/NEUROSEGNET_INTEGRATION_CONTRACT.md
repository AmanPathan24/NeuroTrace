# NeuroSegNet Integration Contract

**Status: Verified & Audited (Phase 0 Reconnaissance Complete)**

## 1. Source Locations & Provenance

| Item | Verified Value | Evidence / Source File |
|---|---|---|
| Original Model Code | `reference_material/model.py`, `reference_material/tumor_segmentation.py` | Line 63: `class UNet3D(nn.Module)` |
| Best Checkpoint Path | `Flairbased_2/model_epoch_45 (1).pt` | File size: 16.29 MB (17,081,028 bytes) |
| Checkpoint Provenance | Trained 3D U-Net over FLAIR Brain MRI (BraTS) | Checkpoint dict: `epoch: 45`, `train_loss: 0.11589`, `val_loss: 0.17561`, `val_dice: [0.99712, 0.46223]` |
| Alternate Checkpoints | `model_epoch_20.pt`, `model_epoch_50.pt`, `model_epoch_55.pt` | Verified in `Flairbased_2/` |
| Reference Pipeline | `reference_material/main.py` | Load FLAIR NIfTI -> Predict -> 3D/2D visualization |

## 2. Model Architecture & Dimensions

| Property | Verified Value | Details |
|---|---|---|
| Model Class | `UNet3D` | 4 encoder levels, bottleneck, 4 decoder levels with skip connections and `crop_or_pad` |
| Initialization Args | `in_channels=1, out_channels=2, base_filters=8, dropout=0.2` | Total parameters: 1,413,250 |
| Total Parameters | 1,413,250 | All trainable weights float32 |
| PyTorch Version | 2.8.0+cpu (compatible with PyTorch 2.0+) | CPU tested and verified |
| Checkpoint Format | PyTorch `.pt` dictionary | Keys: `['epoch', 'model_state_dict', 'optimizer_state_dict', 'train_loss', 'val_loss', 'val_dice']` |
| State Dict Transformation | Strip `module.` prefix | `OrderedDict((k.replace("module.", ""), v) for k, v in sd.items())` |
| Compatibility | Strict load: 0 missing keys, 0 unexpected keys | 136 parameter tensors match 100% |

## 3. Input & Preprocessing Contract

| Property | Verified Value | Notes |
|---|---|---|
| Input Modality | Single FLAIR MRI volume | **Not** a 4-channel BraTS model |
| Supported Format | NIfTI (`.nii`, `.nii.gz`) | Verified with BraTS20 FLAIR scans |
| Input Tensor Shape | `(1, 1, D, H, W)` | Batch=1, Channel=1, Depth, Height, Width |
| Standard BraTS Shape | `(1, 1, 240, 240, 155)` | Matches sample scans in `BRATS/` |
| Normalization | Z-score per volume | `(image - image.mean()) / (image.std() + 1e-8)` |
| Resampling / Patching | Full volume inference | Fits in CPU memory (12.60s on CPU) |

## 4. Output & Postprocessing Contract

| Property | Verified Value | Notes |
|---|---|---|
| Raw Output Shape | `(1, 2, D, H, W)` | Unnormalized raw logits |
| Channel 0 | Background | Voxel argmax 0 |
| Channel 1 | Tumor / Lesion | Voxel argmax 1 |
| Decision Operator | `torch.argmax(output, dim=1)` | Deterministic binary mask `(D, H, W)` |
| Output Mask Values | `{0, 1}` uint8 | 0 = Background, 1 = Tumor |

## 5. Spatial Geometry Contract

- Native NIfTI affine and voxel spacing (`hdr.get_zooms()`) MUST be preserved.
- Output segmentation NIfTI MUST inherit the exact header, affine matrix, and coordinate frame from the input MRI.
- Physical volume formula: `physical_volume_cm3 = sum(mask == 1) * (voxel_x * voxel_y * voxel_z) / 1000.0`.
- Bounding box and centroid MUST distinguish voxel coordinates from world/scanner physical coordinates.

## 6. Golden Inference Test (Verified)

- **Test Subject**: `BRATS/BraTS20_Training_030_flair.nii`
- **Input Shape**: `(240, 240, 155)`, Voxel spacing: `(1.0, 1.0, 1.0)` mm
- **Inference Runtime**: 12.60 seconds on CPU
- **Output Mask Shape**: `(240, 240, 155)`
- **Unique Output Labels**: `[0, 1]`
- **Detected Tumor Voxels**: 67,692 voxels
- **Brain Volume Fraction**: 4.36% (relative to raw voxels > 0: 1,551,130)
- **Physical Volume**: 67.69 mL (cm³)

