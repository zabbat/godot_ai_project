"""Write the ComfyUI API graph that cuts a person or character out of an image, giving a
PNG with a transparent background. Running it (upload, validate, run, download) is done with
comfy-cli, see the comfy-ui-connection skill.

How: YOLO person segmentation (Impact Pack) finds the figure, SAM refines the outline, the
mask is shrunk 1 px (drops a fringe of background colour) and slightly blurred (soft edge),
then joined to the image as its alpha. Everything runs locally; no model is downloaded.

usage:
  cutout.py <image name on the server> <graph.json> [--shrink 1] [--blur 1.0]

<image name on the server> is the name `comfy upload` returned (the file in ComfyUI's input/).
Needs Impact Pack + Impact Subpack, models/ultralytics/segm/person_yolov8m-seg.pt and
models/sams/sam_vit_h_4b8939.pth; `comfy workflow validate` names whatever is missing.
Works best on a figure drawn on a plain background in a colour the figure doesn't have.
"""
import argparse, json

YOLO_MODEL = "segm/person_yolov8m-seg.pt"
SAM_MODEL = "sam_vit_h_4b8939.pth"


def graph(image_name, shrink, blur):
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "2": {"class_type": "UltralyticsDetectorProvider", "inputs": {"model_name": YOLO_MODEL}},
        "3": {"class_type": "SAMLoader", "inputs": {"model_name": SAM_MODEL, "device_mode": "AUTO"}},
        "4": {"class_type": "ImpactSimpleDetectorSEGS",
              "inputs": {"bbox_detector": ["2", 0], "image": ["1", 0], "bbox_threshold": 0.5,
                         "bbox_dilation": 0, "crop_factor": 3.0, "drop_size": 10,
                         "sub_threshold": 0.5, "sub_dilation": 0, "sub_bbox_expansion": 0,
                         "sam_mask_hint_threshold": 0.7, "post_dilation": 0,
                         "sam_model_opt": ["3", 0], "segm_detector_opt": ["2", 1]}},
        "5": {"class_type": "SegsToCombinedMask", "inputs": {"segs": ["4", 0]}},
        # Shrink the mask to drop a fringe of background colour, then soften the hard edge.
        "9": {"class_type": "GrowMask", "inputs": {"mask": ["5", 0], "expand": -shrink,
                                                    "tapered_corners": True}},
        "10": {"class_type": "MaskToImage", "inputs": {"mask": ["9", 0]}},
        "11": {"class_type": "ImageBlur", "inputs": {"image": ["10", 0], "blur_radius": 1,
                                                     "sigma": blur}},
        "12": {"class_type": "ImageToMask", "inputs": {"image": ["11", 0], "channel": "red"}},
        # JoinImageWithAlpha turns 1 - mask into the alpha, so the figure must be 0 in it.
        "6": {"class_type": "InvertMask", "inputs": {"mask": ["12", 0]}},
        "7": {"class_type": "JoinImageWithAlpha", "inputs": {"image": ["1", 0], "alpha": ["6", 0]}},
        "8": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": "cutout/cutout"}},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image", help="image name on the server (from `comfy upload`)")
    parser.add_argument("graph_out", help="where to write the API graph")
    parser.add_argument("--shrink", type=int, default=1, help="pixels to shrink the mask (0: none)")
    parser.add_argument("--blur", type=float, default=1.0, help="edge blur sigma (0.1 = nearly hard)")
    args = parser.parse_args()
    with open(args.graph_out, "w", encoding="utf-8") as f:
        json.dump(graph(args.image, args.shrink, args.blur), f, indent=2)
    print(args.graph_out)


main()
