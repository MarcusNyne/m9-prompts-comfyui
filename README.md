# ComfyUI: m9 Prompts

Custom nodes for [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI). Published to [registry.comfy.org](https://registry.comfy.org/nodes/m9-prompts-comfyui).

### Prompt manipulation
* **[ScramblePrompts \[m9\]](#scrambleprompts-m9-conditioning)**: Reorder prompts, remove prompts, modify weights

* **[TweakWeights \[m9\]](#tweakweights-m9-conditioning)**: Modify the weights of prompts matching keywords

* **[ScramblePromptsText \[m9\]](#scramblepromptstext-m9--tweakweightstext-m9-utils)** / **[TweakWeightsText \[m9\]](#scramblepromptstext-m9--tweakweightstext-m9-utils)**: The same two transforms as text in, text out

* **[StepReplace \[m9\]](#stepreplace-m9-text)**: Rewrite text with up to five search-and-replace steps; support for { a | b } choices

* **[EvaluateStringMultiline \[m9\]](#evaluatestringmultiline-m9-utilitiesprimitive)**: A multiline string primitive that resolves { a | b } choices and can pick a random line

### Prefix builder

* **[Prefix \[m9\]](#prefix-m9-text)**: Join name, theme, scene and frame into a single underscore-separated prefix

### Image utilities

* **[FitPose \[m9\]](#fitpose-m9-imagetransform)**: Fit a pose image into a target canvas without stretching

* **[CropToRatio \[m9\]](#croptoratio-m9-imagetransform)**: Trim an image to an aspect ratio, cutting equally from two opposite edges

* **[CalcScaleFactor \[m9\]](#calcscalefactor-m9-imageupscaling)**: Work out the scale factor, and the 32-pixel-aligned size, that brings an image to a target megapixel count

## ScramblePrompts [m9] (conditioning)

Creates a variation of a text prompt by reordering prompts, removing prompts, and nudging weights up or down.  You may use this node as your positive/negative prompt, or combine with other prompt nodes.

A 'prompt' is a phrase between commas, but not inside of parenthesis.  If you have parenthesis between commas, it is considered a single prompt.  For example:
- prompt one, prompt two
- prompt (one), prompt two
- (prompt, one), prompt two

### Input Connectors

   * **clip**: Input. Standard clip connector
   * **conditioning_optional**: Input (optional). If you have another prompt node, you may combine the output of both nodes by connecting the CONDITIONING output of the other node into this input.
   * **seed_optional**: Input (optional).  Connect a seed primitive so the node is reevaluated on each run, rather than ComfyUI reusing its cached result.
     * The same seed always produces the same variation, so a result you like can be reproduced

### Output Connectors

   * **CONDITIONING**: Output. Standard output. Connect this to your KSampler input.

### Settings

   * **prompt**: This is the text prompt that will be modified to create a variation. The extent to which the text prompt is modified depends on the modifiers below.
   * **print_output**: When enabled, the modified prompt is sent to the command window.

#### Prompt Order

  * **order_prompts_percent**: The percent of prompts to reorder.

#### Prompt Reduction

   * **remove_prompts_percent**: The number of prompts to remove.
     * prompts are removed entirely
     * Does not include Loras
   * **keep_prompts**: A list of keywords for prompts to keep.
     * As long as a prompt includes the specified keyword, it will not be removed
     * Comma delimited

#### Prompt Weight

   * **modify_weights_percent**: The percent of prompts that will have the weight changed.
   * **weight_range**: The maximum amount to modify the weight in either direction.
     * If a change would take the weight below zero, the weight will be left as is
   * **max_weight**: Maximum final weight.
     * When a change will take the weight over the max, the change is not made
     * For example, if the weight is 1, the max is 1.2, and the change is +0.3, the weight will be left at 1

## TweakWeights [m9] (conditioning)

Adjusts the weight of prompts matching your keywords, leaving every other prompt untouched.  Where **ScramblePrompts** varies the whole prompt, this node targets the parts you name.  You may use this node as your positive/negative prompt, or combine with other prompt nodes.

Prompts are split on commas exactly as described for **ScramblePrompts** above, with anything inside parenthesis kept together as a single prompt.

### Input Connectors

   * **clip**: Input. Standard clip connector
   * **conditioning_optional**: Input (optional). If you have another prompt node, you may combine the output of both nodes by connecting the CONDITIONING output of the other node into this input.
   * **seed_optional**: Input (optional).  Connect a seed primitive so the node is reevaluated on each run, rather than ComfyUI reusing its cached result.
     * The same seed always produces the same variation, so a result you like can be reproduced

### Output Connectors

   * **CONDITIONING**: Output. Standard output. Connect this to your KSampler input.

### Settings

   * **prompt**: This is the text prompt containing the prompts to be modified.
   * **keywords**: A list of keywords identifying which prompts to modify.
     * Comma delimited
     * A prompt is modified if it matches any one of the keywords
     * Matching is case insensitive, and matches anywhere within the prompt, so `hair` also matches `long hair` and `hairband`
     * When left empty, no weights are changed and the prompt is used as is
   * **weight_range**: The maximum amount to modify the weight in either direction.
     * The adjustment is random, anywhere between minus and plus this amount
     * If a change would take the weight below zero, the weight will be left as is
   * **max_weight**: Maximum final weight.
     * When a change will take the weight over the max, the change is not made
     * For example, if the weight is 1, the max is 1.2, and the change is +0.3, the weight will be left at 1
   * **print_output**: When enabled, each changed prompt is sent to the command window, along with its weight before and after.

Lora weights are never changed, even when a lora matches one of your keywords.

## ScramblePromptsText [m9] / TweakWeightsText [m9] (utils)

Text-in, text-out versions of the two nodes above.  They apply exactly the same transforms, but take a
STRING input and return the rewritten prompt as a STRING, with no **clip** and no CONDITIONING.

Use these when you want the rewritten text before it is encoded: to feed a stock "CLIP Text Encode
(prompt)" node, to chain the two transforms together (scramble the whole prompt, then tweak the weights of
the parts you name), or to send the result to a preview/save node so you can see what was generated.

### Input Connectors

   * **prompt**: Input. The text prompt to modify.  This is an input connector rather than a text field, so
     the text itself lives in whatever node feeds it — a primitive string node, another prompt node, or one
     of these nodes.
   * **seed_optional**: Input (optional).  Works exactly as it does on the CONDITIONING nodes.

### Output Connectors

   * **prompt**: Output (STRING). The modified prompt.

### Settings

The settings are identical to **ScramblePrompts [m9]** and **TweakWeights [m9]** respectively; see those
sections above.  **print_output** sends the same information to the command window.

## StepReplace [m9] (text)

Rewrites a text prompt with up to five search-and-replace steps, and collapses any `{ one | two }` choice it meets along the way down to a single randomly picked option.  Useful for prompt templates: keep the wording in one node, and swap placeholders such as `[SUBJECT]` or `[OUTFIT]` for the text you actually want, or for a random pick out of a short list.

### Connectors

   * **text**: Input (STRING). The text to rewrite.  This is an input rather than a field, so the text lives in whatever node feeds it -- a primitive, another prompt node, or any node that outputs a string.
   * **seed_optional**: Input (INT, optional). Seeds the random choices.  See below.
   * **text**: Output (STRING). The rewritten text.  Feed it to a CLIP Text Encode node, or on to another text node.

### Fields

   * **search_1** \ **replace_1** ... **search_5** \ **replace_5**: Five search-and-replace pairs, applied in order.  **search** is a single line, **replace** is multi-line.
   * **print_output**: Prints what each step did, and the final text, to the console window.

### Steps run top to bottom

Each step works on the result of the step before it, so a later **search** can find text that an earlier **replace** produced:

| step | pair | result |
|---|---|---|
| text | | `a flower in a vase` |
| step 1 | `flower` -> `rose` | `a rose in a vase` |
| step 2 | `rose` -> `red rose` | `a red rose in a vase` |

   * A step with an empty **search** is skipped, so you can use only as many of the five as you need
   * An empty **replace** deletes the search term
   * Every occurrence is replaced, not just the first

Search terms are matched literally and are not case sensitive, so `cat` also finds `Cat` and `CAT`.  A term that begins or ends with a letter, digit or underscore only matches whole words -- `cat` does not find the `cat` inside `category`.  A term wrapped in anything else matches wherever it appears, so placeholders like `[FIND_THIS]` and terms like `<lora:foo:0.8>` work exactly as written.

### Random choices

Anywhere in the incoming text, or in a **replace** field, `{ one | two | three }` collapses to exactly one of the options:

   * Options are trimmed, so `{ a | b }` and `{a|b}` are the same thing
   * An empty option is allowed: `{ a | }` picks either `a` or nothing at all
   * Choices may be nested: `{ a | { b | c } }`
   * Each field picks once, so one replacement used three times gives the same result all three times
   * Braces without a `|` are left alone, and `\{` `\|` `\}` are literal characters rather than choice syntax

Every choice is resolved before any search and replace runs -- the incoming text first, then each **replace** field -- so each field settles on one option up front.  A `[EYE_COLOR]` placeholder that appears three times, replaced with `{ blue | green }`, comes out as three blue eyes or three green eyes, never a mix.

A later **search** can still match the option an earlier choice picked.  In the example above, replacing `flower` with `{ rose | tulip }` means step 2 only fires on the runs where `rose` came up.

### Seeding

   * With **seed_optional** left unconnected (or set to `0`), a fresh random seed is used on every run, and the node is re-evaluated each time rather than serving a cached result
   * With any other seed the run is fully reproducible: the same seed and the same fields always produce the same text
   * Connect a seed primitive to reproduce a specific result later from the numbers saved in the workflow

## EvaluateStringMultiline [m9] (utilities/primitive)

A multiline text box, like the stock String (Multiline) primitive, with two additions: `{ one | two }` choices are resolved, and one line of the result can be picked at random.  Useful for keeping a list of options -- outfits, settings, whole prompts -- in one place and drawing from it each run.

### Connectors

   * **seed_optional**: Input (INT, optional). Seeds the random choices and the random line.  Works exactly as it does on **StepReplace [m9]**: left at `0`, a fresh seed is used and the node is re-evaluated every run; any other seed makes the result reproducible.
   * **text**: Output (STRING). The whole text, with every choice resolved.
   * **random_line**: Output (STRING). One line of **text**, picked at random.

### Fields

   * **value**: The text.  Choices follow the same rules as in **StepReplace [m9]**: options are trimmed, may be empty, may be nested, and `\{` `\|` `\}` are literal characters.

### Random line

   * The line is picked from the resolved text, so it always matches one of the lines of the **text** output
   * Surrounding whitespace is trimmed, and blank lines are never picked
   * With only one line, that line is always returned
   * With no text at all, **random_line** is empty

## Prefix [m9] (text)

Builds a single string out of up to four parts, joined with underscores.  Intended for the **filename_prefix** field of a SaveImage node, so a batch of renders can be named consistently.

### Connectors

   * **prefix**: Output (STRING). The joined text.  Connect it to the **filename_prefix** input of a SaveImage node (convert that widget to an input first).

### Fields

   * **name** \ **theme** \ **scene** \ **frame**: The four parts, joined in that order.
     * Each one is optional; leave a field empty and it is skipped, along with its separator
     * With only **name** filled in, the output has no underscores at all
     * With **name** and **scene** filled in, the output is `name_scene`
     * Any of these may be converted to an input and driven by another node

When every field is empty the output is `ComfyUI`, which is the same default SaveImage uses on its own, so an unconfigured node still produces valid file names.

Values are cleaned up before joining: surrounding whitespace is trimmed, and characters that are illegal in a file name (`< > : " / \ | ? *`) are replaced with an underscore.  Note that this also applies to ComfyUI's own `%date:yyyy-MM-dd%` prefix tokens and to forward slashes used for subfolders — both contain characters that get replaced, so build those into the SaveImage field directly rather than through this node.

## FitPose [m9] (image/transform)

Fits a pose/control image (such as an OpenPose skeleton on a black background) into a target canvas size without stretching.  The image is scaled to fit, placed on the canvas, and padded with black.

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

## CropToRatio [m9] (image/transform)

Trims an image down to a target aspect ratio.  Intended for tidying up a crop taken from a bounding box: the crop comes out at whatever shape the box happened to be, and this brings it back to the ratio the rest of the workflow expects.

Nothing is scaled and nothing is added.  One axis is trimmed equally from both ends until what remains matches the ratio: an image that is too wide loses its left and right edges, one that is too tall loses its top and bottom.  When the number of pixels to remove is odd, the extra one comes off the bottom or the right.

### Connectors

   * **image**: Input. The image to crop.
   * **width** / **height**: Inputs (INT, optional). The target ratio.  Drive them from a primitive, or from the width/height outputs of a node such as FitPose [m9].
   * **ratio_image**: Input (optional). When connected, the target ratio is taken from this image and the width/height inputs are ignored.  Only its proportions are read, never its pixels — wire in the latent-sized image, the original frame, or anything else already at the shape you want to match.
   * **IMAGE**: Output. The cropped image.
   * **width** / **height**: Outputs (INT). The size of the cropped image, or of the original when it passes through unchanged.
   * **megapixels**: Output (FLOAT). The cropped image's pixel count in millions (width × height ÷ 1,000,000).

With neither **ratio_image** nor **width**/**height** connected there is no ratio to crop to, and the image passes through unchanged.

### Fields

   * **mode**: Which images get cropped at all.
     * `Always` (default) crops every image, even when that turns a tall image into a wide one
     * `Vertical only` crops a portrait image and leaves it portrait
     * `Horizontal only` crops a landscape image and leaves it landscape
     * Neither restricted mode ever changes an image's orientation.  A portrait image with a landscape target ratio would have to come out landscape, so under `Vertical only` it passes through untouched instead — and a landscape image is left alone in that mode regardless of the ratio
     * Square counts as neither, so a square image, or a target ratio that comes out square, passes through under both restricted modes

Only the ratio matters, never the size: `1216` x `832` and `152` x `104` produce exactly the same crop.  An image already at the target ratio passes through unchanged, as does one whose ratio is zero on either side.  Batches are supported — every frame shares a size, so the whole batch is cropped identically.

### Typical use

A detection node hands you a bounding box, an ImageCrop gives you the region, and you want to send it through a generation pass that expects a particular shape.  The crop is whatever shape the box was, so put this node between the two:

```
ImageCrop  ──image──►  CropToRatio [m9]  ──image──►  upscale / detailer / encode
                              ▲
  reference image or size ────┘   (ratio_image, or width + height)
```

The result still needs resizing to the exact pixel dimensions — this node only fixes the *shape*, never the size, so the resize that follows it is no longer a stretch.

### Choosing a mode

Reach for a restricted mode when the ratio you are matching does not always agree with the images you are feeding it:

   * **`Always`** when every image should end up at the target ratio, whatever it takes.  A tall crop against a wide ratio loses most of its height and comes out wide.
   * **`Vertical only`** when you are matching a portrait ratio and want anything already landscape left alone — full-body crops trimmed to a portrait canvas, say, while a wide establishing shot passes straight through.
   * **`Horizontal only`** for the mirror case.

The restricted modes are a filter, not a different crop: an image they do crop is cropped exactly as `Always` would have.  They only ever decline.  So if a workflow is mysteriously not cropping, the mode is the first thing to check — an orientation that disagrees with the ratio is a silent pass-through by design, not an error.

## CalcScaleFactor [m9] (image/upscaling)

Works out how much to scale an image by to reach a target megapixel count, with the resulting size locked to a 32-pixel grid.  Nothing is resized here — this node only does the arithmetic, for an Upscale Image By or an Upscale Image node downstream to act on.

### Connectors

   * **image**: Input (optional). When connected, the size is taken from this image and the width/height inputs are ignored.  Only its size is read, never its pixels.
   * **width** / **height**: Inputs (INT, optional). The size to scale from, used only when **image** is not connected.
   * **scale_factor**: Output (FLOAT). The factor to scale by.  Scaling by it lands the width exactly on the **width** output.
   * **width** / **height**: Outputs (INT). The target size, both multiples of 32.

With neither **image** nor **width**/**height** connected there is no size to work from: **scale_factor** is `1.0` and **width**/**height** are `0`.

### Fields

   * **megapixels**: The target size in millions of pixels.  `1.0` is about the size of 1024 x 1024.

### How close it gets

The 32-pixel grid takes priority over the megapixel target, so the result is close but rarely exact: a 1920 x 1080 image at `1.0` comes out at 1344 x 768, which is 1.03 MP.

One factor applied to both sides can only land both of them on the grid for a few aspect ratios, so the **width** is the one guaranteed.  The **height** output is the multiple of 32 nearest to where the factor puts the height, which is never more than 16 pixels away (1920 x 1080 scaled by `0.7` is 1344 x 756, against a **height** output of 768).  When both sides must be exact, feed the **width**/**height** outputs to a resize node instead of using **scale_factor** — the aspect ratio shifts by those few pixels.

## Example Workflows

Example workflows are embedded in the four images in the [examples](examples) folder.  Drag one into ComfyUI to load the workflow it was generated with.

### [ScramblePrompts_Conditioning_m9.png](examples/ScramblePrompts_Conditioning_m9.png)

In this example workflow, the positive "CLIP Text Encode (prompt)" is replaced with a **ScramblePrompts [m9]** node.  ComfyUI will cache the results of nodes to make generation more efficient.  If you use this node without an input into **seed_optional**, the prompts will only be randomized the first time, with the results cached and reused.

By adding a seed primitive, and connecting it to **seed_optional**, the node will be reevaluated for each run, resulting in a different result for each image.

**print_output** is enabled, allowing you to see the results of prompt scrambling in the console window.

The file name comes from the use of **Prefix [m9]**.

### [ScramblePrompts_ClipConditioning_m9.png](examples/ScramblePrompts_ClipConditioning_m9.png)

In this example, the **ScramblePrompts [m9]** node is used in conjunction with the existing positive "CLIP Text Encode (prompt)".  The prompts within the text encoder are left as is, and the scrambled prompts are added to them in the final prompt sent to the sampler.

### [ScramblePrompts_TextPreview_m9.png](examples/ScramblePrompts_TextPreview_m9.png)

This example uses the **ScramblePromptsText [m9]** variant where the output text goes into a "CLIP Text Encode" node for conditioning.  The text output can be previewed.

### [StepReplace_TextPreview_m9.png](examples/StepReplace_TextPreview_m9.png)

This example uses **StepReplace [m9]** to perform multiple text replacements and show a text preview.

This can be used to individually control the inclusion of text parts of a prompt from a main prompt.

An incrementing seed is used on every run, and the node is re-evaluated each time rather than serving a cached result.