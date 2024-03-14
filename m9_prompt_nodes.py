from .m_prompt import *

class Color9:
    codes = None

    @staticmethod
    def AddCode(inCode, inValue):
        Color9.codes[inCode] = inValue

    @staticmethod
    def GetCode(inCode):
        if inCode in Color9.codes:
            return Color9.codes[inCode]
        return ""
    
    @staticmethod
    def InitColors():
        if Color9.codes is None:
            Color9.codes = {}
            Color9.codes['END'] = '\33[0m'
            Color9.codes['BOLD'] = '\33[1m'
            Color9.codes['ITALIC'] = '\33[3m'
            Color9.codes['UNDERLINE'] = '\33[4m'
            Color9.codes['RED'] = '\33[31m'
            Color9.codes['GREEN'] = '\33[32m'
            Color9.codes['YELLOW'] = '\33[33m'
            Color9.codes['BLUE'] = '\33[34m'
            Color9.codes['VIOLET'] = '\33[35m'
            Color9.codes['WHITE'] = '\33[37m'
            Color9.codes['LIGHTRED'] = '\33[91m'
            Color9.codes['LIGHTGREEN'] = '\33[92m'
            Color9.codes['LIGHTYELLOW'] = '\33[93m'
            Color9.codes['LIGHTBLUE'] = '\33[94m'
            Color9.codes['LIGHTVIOLET'] = '\33[95m'
            Color9.codes['LIGHTWHITE'] = '\33[97m'

    def __init__(self, inSystem=None):
        Color9.InitColors()
        self.system = inSystem

    def Message(self, inString):
        print(self.sysstr() + Color9.GetCode("WHITE") + inString + Color9.GetCode("END"))

    def Warning(self, inString):
        wstr = Color9.GetCode("LIGHTRED") + "[WARNING] "
        print(self.sysstr() + wstr + Color9.GetCode("WHITE") + inString + Color9.GetCode("END"))

    def Header(self, inString=None):
        s1 = " ***"
        s2 = ""
        if inString is None:
            inString = ""
        else:
            s1 = ""
            s2 = ": "
        print(self.sysstr(inCode="VIOLET", inPrefix="*** ", inPostfix=s1) + Color9.GetCode("LIGHTVIOLET") + s2 + inString + Color9.GetCode("END"))

    def Print(self, inString, inCode):
        print(Color9.GetCode(inCode) + inString + Color9.GetCode("END"))

    def sysstr(self, inCode="BLUE", inPrefix="", inPostfix=": "):
        if self.system is not None:
            return Color9.GetCode(inCode)+inPrefix+self.system+inPostfix
        return ""


class ScramblePrompts_m9:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"prompt": ("STRING", {"multiline": True}),
                                "clip": ("CLIP", ),
                                "order_prompts_percent": ("INT", {"default": 20, "min": 0, "max": 100, "step": 5, "display": "slider"}),
                                "remove_prompts_percent": ("INT", {"default": 0, "min": 0, "max": 30, "step": 5, "display": "slider"}),
                                "keep_prompts": ("STRING", {"multiline": False}),
                                "modify_weights_percent": ("INT", {"default": 20, "min": 0, "max": 100, "step": 5, "display": "slider"}),
                                "weight_range": ("FLOAT", {"default": 0.5, "min": 0, "max": 2, "step": 0.1}),
                                "max_weight": ("FLOAT", {"default": 1.9, "min": 0, "max": 3, "step": 0.1}),
                                "print_output": ("BOOLEAN", {"default": False}),
                            },
                "optional":{"conditioning_optional": ("CONDITIONING", ),
                            "seed_optional": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                            }}

    RETURN_TYPES = ("CONDITIONING", ) #"STRING",)

    FUNCTION = "encode"

    CATEGORY = "M9 Prompts"

    def encode(self, clip, prompt, order_prompts_percent, remove_prompts_percent, keep_prompts, modify_weights_percent, weight_range, max_weight, print_output, conditioning_optional=None, seed_optional=None):
        mp = mPrompt(inSeed=seed_optional, inPrompt=prompt)
        cnt_prompts = mp.CountTokens('prompt')
        if order_prompts_percent>0:
            mp.ScrambleOrder(inLimit=int((order_prompts_percent*cnt_prompts)/100))
        if remove_prompts_percent>0:
            mp.ScrambleReduction(inTarget=int((remove_prompts_percent*cnt_prompts)/100), inKeepTokens=keep_prompts)
        if modify_weights_percent>0:
            mp.ScrambleWeights(weight_range, inIsLora=False, inLimit=int((modify_weights_percent*cnt_prompts)/100), inMinOutput=0, inMaxOutput=max_weight)
            
        final_text = mp.Generate()
        if print_output:
            clr = Color9("ScramblePrompts [m9]")
            clr.Header()
            clr.Print(final_text, "LIGHTVIOLET")
            # print(mp.GetLog())
        tokens = clip.tokenize(final_text)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        cond_list = [[cond, {"pooled_output": pooled}]]
        if conditioning_optional is not None:
            cond_list = conditioning_optional + cond_list
        # return (cond_list, final_text, )
        return (cond_list, )
    #@classmethod
    #def IS_CHANGED(s, image, string_field, int_field, float_field, print_to_screen):
    #    return ""

class TweakWeights_m9:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"prompt": ("STRING", {"multiline": True}),
                                "clip": ("CLIP", ),
                                "keywords": ("STRING", {"multiline": False}),
                                "weight_range": ("FLOAT", {"default": 0.5, "min": 0, "max": 2, "step": 0.1}),
                                "max_weight": ("FLOAT", {"default": 1.9, "min": 0, "max": 3, "step": 0.1}),
                                "print_output": ("BOOLEAN", {"default": False}),
                            },
                "optional":{"conditioning_optional": ("CONDITIONING", ),
                            "seed_optional": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                            }}

    RETURN_TYPES = ("CONDITIONING", ) #"STRING",)

    FUNCTION = "encode"

    CATEGORY = "M9 Prompts"

    def encode(self, clip, prompt, keywords, weight_range, max_weight, print_output, conditioning_optional=None, seed_optional=None):
        mp = mPrompt(inSeed=seed_optional, inPrompt=prompt)
        if keywords!="":
            mp.TweakWeights(keywords, inRange=weight_range, inLoraRange=0, inMaxOutput=max_weight)
            
        final_text = mp.Generate()
        if print_output:
            clr = Color9("TweakWeights [m9]")
            clr.Header()
            if keywords=="":
                clr.Warning("Keywords is empty.  Specify keywords to tweak weights (comma delimited).")
            else:
                clr.Print(mp.GetLog(), "LIGHTVIOLET")
        tokens = clip.tokenize(final_text)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        cond_list = [[cond, {"pooled_output": pooled}]]
        if conditioning_optional is not None:
            cond_list = conditioning_optional + cond_list
        # return (cond_list, final_text, )
        return (cond_list, )
    #@classmethod
    #def IS_CHANGED(s, image, string_field, int_field, float_field, print_to_screen):
    #    return ""


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "ScramblePrompts_m9": ScramblePrompts_m9,
    "TweakWeights_m9": TweakWeights_m9
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "ScramblePrompts_m9": "ScramblePrompts [m9]",
    "TweakWeights_m9": "TweakWeights [m9]"
}

Color9("m9 Prompts").Message("Loaded")
# c = Color9("M9 Prompts")
# c.Message("Loaded")
# c.Warning("warning")
# c.Header()
# c.Header("info prompt")
# c.Print('VIOLET', 'VIOLET')
# c.Print('LIGHTVIOLET', 'LIGHTVIOLET')
