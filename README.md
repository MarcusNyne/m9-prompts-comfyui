# ComfyUI: m9 Prompts

Custom nodes for [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI).

Two custom nodes are included for modifying a prompt to create prompt variations.
   * ScramblePrompts [m9]: Reorder prompts, remove prompts, modify weights
   * TweakWeights [m9]: Modify the weights of prompts matching keywords

An image node is also included for preparing pose/control images.
   * FitPose [m9]: Fit a pose image into a target canvas without stretching

## Overview

You may use these nodes as your positive/negative prompt, or combine them with other prompt nodes.

### Common Connectors (prompt nodes)

   * **clip**: Input. Standard clip connector
   * **conditioning_optional**: Input (optional). If you have another prompt node, you may combine the output of both nodes by connecting the CONDITIONING output of the other node into this input.
   * **CONDITIONING**: Output. Standard output. Connect this to your KSampler input.
   * **seed_optional**: Input (optional).  Recommended to convert this to an input when you want the variation to be deterministic based on the seed.  Otherwise, the same seed could produce different variants.

### Common Fields (prompt nodes)

   * **prompt**: This is the text prompt that will be modified to create a variation. The extent to which the text prompt is modified depends on node settings.
   * **print_output**: When enabled, output will be sent to the command window describing the new prompt.

## ScramblePrompts [m9] 

Modifications to the prompt may include:
   * Changing the order of prompts
   * Removing prompts
   * Changing the weight of prompts

A 'prompt' is a phrase between commas, but not inside of parenthesis.  If you have parenthesis between commas, it is considered a single prompt.  For example:
- prompt one, prompt two
- prompt (one), prompt two
- (prompt, one), prompt two

### Prompt Order

  * **order_prompts_percent**: The percent of prompts to reorder.

### Prompt Reduction

   * **remove_prompts_percent**: The number of prompts to remove.
     * prompts are removed entirely
     * Does not include Loras
   * **keep_prompts**: A list of keywords for prompts to keep.
     * As long as a prompt includes the specified keyword, it will not be removed
     * Comma delimited

### Prompt Weight

   * **modify_weights_percent**: The percent of prompts that will have the weight changed.
   * **weight_range**: The maximum amount to modify the weight in either direction.
     * If a change would take the weight below zero, the weight will be left as is
   * **max_weight**: Maximum final weight.
     * When a change will take the weight over the max, the change is not made
     * For example, if the weight is 1, the max is 1.2, and the change is +0.3, the weight will be left at 1

## FitPose [m9]

Fits a pose/control image (such as an OpenPose skeleton on a black background) into a target canvas size without stretching.  The image is scaled to fit, placed on the canvas, and padded with black.

Found under the **image/transform** category.

### Connectors

   * **image**: Input. The pose/control image to fit.
   * **latent**: Input (optional). When connected, the canvas size is taken from the latent and the width/height fields are ignored.
   * **IMAGE**: Output. The fitted image.
   * **width** / **height**: Outputs (INT). The resolved canvas size, handy for wiring into an EmptyLatentImage node so the pipeline stays in sync.

### Fields

   * **subscale**: Margin control.
     * `1.0` scales the image so it touches the canvas edge exactly, with no margin
     * `0.8` scales to 80% of that, leaving a proportional margin around the image
     * Above `1.0` the image overflows and is cropped by the canvas edges
   * **placement**: Where the image sits when it does not fill the canvas: centered, bottom, left, right, bottom-left, or bottom-right.
     * `centered` (default) is the original behaviour
     * `bottom` keeps a figure standing on the bottom edge, with the margin above it
     * Has no visible effect at `subscale` `1.0`, since the image already fills the canvas on both axes
     * Above `1.0` it decides which side is cropped: `left` keeps the left edge and crops the right
   * **interpolation**: Resampling filter: lanczos, bicubic, bilinear, or nearest.
     * `lanczos` (default) is a good general choice
     * `nearest` preserves hard skeleton lines without anti-aliasing softness
   * **width** / **height**: The canvas size to fit into, used only when **latent** is not connected.

The aspect ratio of the input image is always preserved.  A smaller image is scaled up to fit the canvas, so **placement** only matters once **subscale** moves away from `1.0`.  Batches are supported, with each image fitted independently.

## Example Workflows

Example workflows can be found in the two included example images, that use the **ScramblePrompts [m9]** node.

## ScramblePromptsExample-1.png

In this example workflow, the positive "CLIP Text Encode (prompt)" is replaced with a **ScramblePrompts [m9]** node.  ComfyUI will cache the results of nodes to make generation more efficient.  If you use this node without an input into **seed_optional**, the prompts will only be randomized the first time, with the results cached and reused.

By adding a seed primitive, and connecting it to **seed_optional**, the node will be reevaluated for each run, resulting in a different result for each image.

**print_output** is enabled, allowing you to see the results of prompt scrambling in the console window.

## ScramblePromptsExample-2.png

In this example, the **ScramblePrompts [m9]** node is used in conjunction with the existing positive "CLIP Text Encode (prompt)".  The prompts within the text encoder and left as is, and the scrambled prompts are added to them in the final prompt sent to the sampler.

## Help and Feedback

   * **Discord Server**
     * https://discord.gg/trMfHcTcsG

## m9 Prompts Catalog

   * **Scramble Prompts for Stable Diffusion**
     * Works with Automatic1111
     * Reorder, remove, modify weights of prompts
     * https://github.com/MarcusNyne/sd-scramble-prompts-m9

   * **Tweak Weights for Stable Diffusion**
     * Works with Automatic1111
     * Modify prompt weights using keywords
     * https://github.com/MarcusNyne/sd-tweak-weights-m9

   * **m9 Prompts for ComfyUI**
     * Works with ComfyUI
     * Includes nodes for Scramble Prompts, Tweak Weights, and Fit Pose
     * https://github.com/MarcusNyne/m9-prompts-comfyui
