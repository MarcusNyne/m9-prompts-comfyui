# ComfyUI: m9 Prompts

Custom nodes for [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI).

* **ScramblePrompts [m9]**: Reorder prompts, remove prompts, modify weights

* **TweakWeights [m9]**: Modify the weights of prompts matching keywords

* **ScramblePromptsText [m9]** / **TweakWeightsText [m9]**: The same two transforms as text in, text out

* **FitPose [m9]**: Fit a pose image into a target canvas without stretching

* **Prefix [m9]**: Join name, theme, scene and frame into a single underscore-separated prefix

* **StepReplace [m9]**: Rewrite text with up to five search-and-replace steps, with random { a | b } choices

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
   * Each occurrence draws on its own, so one replacement used three times can give three different results
   * Braces without a `|` are left alone, and `\{` `\|` `\}` are literal characters rather than choice syntax

Choices are resolved as the text is built, not at the end, so a later **search** can also match the option a choice picked.  In the example above, replacing `flower` with `{ rose | tulip }` means step 2 only fires on the runs where `rose` came up.

### Seeding

   * With **seed_optional** left unconnected (or set to `0`), a fresh random seed is used on every run, and the node is re-evaluated each time rather than serving a cached result
   * With any other seed the run is fully reproducible: the same seed and the same fields always produce the same text
   * Connect a seed primitive to reproduce a specific result later from the numbers saved in the workflow

## Example Workflows

Example workflows can be found in the two included example images, that use the **ScramblePrompts [m9]** node.

### ScramblePromptsExample-1.png

In this example workflow, the positive "CLIP Text Encode (prompt)" is replaced with a **ScramblePrompts [m9]** node.  ComfyUI will cache the results of nodes to make generation more efficient.  If you use this node without an input into **seed_optional**, the prompts will only be randomized the first time, with the results cached and reused.

By adding a seed primitive, and connecting it to **seed_optional**, the node will be reevaluated for each run, resulting in a different result for each image.

**print_output** is enabled, allowing you to see the results of prompt scrambling in the console window.

### ScramblePrompts_m9_00001_.png

In this example, the **ScramblePrompts [m9]** node is used in conjunction with the existing positive "CLIP Text Encode (prompt)".  The prompts within the text encoder are left as is, and the scrambled prompts are added to them in the final prompt sent to the sampler.

The file name comes from the use of **Prefix [m9]**.
