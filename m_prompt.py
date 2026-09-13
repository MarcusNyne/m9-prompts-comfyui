import random

class mPrompt:

    sLineSplit = 120

    def __init__(self, inSeed=None, inPrompt=None) -> None:
        self.seed = inSeed
        # Seed once, here, and draw from a private generator for the life of this object.
        # Seeding before each individual draw would rewind the sequence every time, so every
        # draw would return the same number (identical weight deltas, r1==r2 in ScrambleOrder).
        # A private Random also keeps a caller-supplied seed from resetting the global RNG,
        # which is shared with the rest of the process.  Random(None) seeds from entropy, so
        # an unseeded mPrompt stays fully random.
        self.rng = random.Random(inSeed)
        self.Reset()
        if inPrompt is not None:
            self.__init_prompt(inPrompt)

    def CountTokens(self, inCategory:str=None):
        if inCategory is None:
            return len(self.p_prompts)
        
        cnt = 0
        for p in self.p_prompts:
            match inCategory:
                case 'prompt':
                    if 'lora' not in p:
                        cnt += 1
                case 'lora':
                    if 'lora' in p:
                        cnt += 1

        return cnt

    def LoadPrompt(self, inFilePath:str) -> bool:
        self.Reset()
        try:
            f = open(inFilePath, "rt")
            lines = f.readlines()
            f.close()
            self.__init_prompt("\n".join(lines))

        except OSError:
            return False

        return True

    def SavePrompt(self, inFilePath:str, inLog:bool=False) -> bool:
        if type(self.p_output) is not str:
            return False

        try:
            f = open(inFilePath, "wt")
            f.write(self.p_output)
            if inLog is True:
                f.write("\n\n")
                f.write(self.GetLog())
            f.close()

        except OSError:
            return False

        return True

    def GetLog(self):
        log = ""
        for l in self.p_log:
            if not l.startswith("="):
                log += "\t"
            log += l+"\n"
        return log

    def Reset(self):
        self.p_string = ""
        self.p_prompts = []
        self.p_log = []
        self.__reset_generation()

    def ScrambleOrder(self, inLimit=None, inVariance:int=None):
        # limit None scrambles the entire list
        # if limit is specified, only a limited number are reordered
        if inLimit==0:
            return
        if inLimit is None:
            self.rng.shuffle(self.p_prompts)
            self.__log_header("All prompts reordered")
        elif type(inLimit) is int:
            if inVariance is not None:
                inLimit += self.rng.randint(0, inVariance*2) - inVariance
                inLimit = max(inLimit, 0)

            ln = len(self.p_prompts)
            pmap = list(range(ln))
            reordered = []
            while inLimit>0 and len(reordered)<ln:
                r1=0
                r2=0
                try_cnt = 0
                while try_cnt<ln*3 and (r1==r2 or pmap[r1] in reordered):
                    r1 = self.rng.randrange(0, ln)
                    r2 = self.rng.randrange(0, ln)
                    try_cnt += 1
                if try_cnt>=ln*3:
                    break

                reordered.append(pmap[r1])

                pmap = self.__shift(pmap, r1, r2)
                inLimit -= 1

            cnt = 0
            for r in range(len(pmap)):
                if pmap[r] in reordered and pmap[r]!=r:
                    cnt += 1

            if cnt>0:
                self.__log_header("{} prompts reordered".format(cnt))

                for r in range(len(pmap)):
                    if pmap[r] in reordered and pmap[r]!=r:
                        # p_prompts is still in the old order here, so the prompt that
                        # ends up at position r is the one at index pmap[r], not r.
                        if r<pmap[r]:
                            self.__log_entry(self.p_prompts[pmap[r]]['token'], "Moved up by {cnt}".format(cnt=pmap[r]-r))
                        else:
                            self.__log_entry(self.p_prompts[pmap[r]]['token'], "Moved down by {cnt}".format(cnt=r-pmap[r]))

                tks = []
                for r in range(ln):
                    tks.append(self.p_prompts[pmap[r]])
                self.p_prompts = tks

    def ScrambleWeights(self, inRange:float, inIsLora=False, inLimit=None, inVariance=None, inMinInput:float=None, inMaxInput:float=None, inMinOutput:float=None, inMaxOutput:float=None):
        ln = len(self.p_prompts)

        pmap = []
        for x in range(ln):
            # An opaque phrase carries [ ] or { } syntax owned by another processor.
            # Its weight can never be emitted, so changing it would only be noise.
            if 'opaque' in self.p_prompts[x]:
                continue
            if inIsLora is False and 'lora' not in self.p_prompts[x]:
                pmap.append(x)
            elif inIsLora is True and 'lora' in self.p_prompts[x]:
                pmap.append(x)

        ln = len(pmap)
        if ln==0:
            return

        target = "prompt" if inIsLora is False else "lora"
        self.rng.shuffle(pmap)
        if inLimit is None:
            self.__log_header("All {target} weights changed ({range:0.1f})".format(target=target, range=inRange))
        else:
            inLimit = min(inLimit, ln)
            if inVariance is not None:
                inLimit += self.rng.randint(0, inVariance*2) - inVariance
                inLimit = max(inLimit, 0)
            self.__log_header("{limit} {target} weights changed ({range:0.1f})".format(target=target, limit=inLimit, range=inRange))
            pmap = pmap[:inLimit]

        for p in pmap:
            weight = self.p_prompts[p]['weight'] if 'weight' in self.p_prompts[p] else 1
            self.p_prompts[p]['weight'] = self.__modify_weight(weight, inRange, inMinInput=inMinInput, inMaxInput=inMaxInput, inMinOutput=inMinOutput, inMaxOutput=inMaxOutput)
            self.__log_weight(self.p_prompts[p]['token'], weight, self.p_prompts[p]['weight'])

    def TweakWeights(self, inKeywords:str, inRange:float, inLoraRange:float, inMaxOutput:float=None):
        self.__log_header("Weights changed for: {keywords} ({range:0.1f}/{lorarange:0.1f})".format(keywords=inKeywords, range=inRange, lorarange=inLoraRange))
        keywords = []
        for kw in inKeywords.split(','):
            kw = kw.lower().strip()
            if kw!="":
                keywords.append(kw)

        ln = len(self.p_prompts)
        for x in range(ln):
            if 'opaque' in self.p_prompts[x]:
                continue
            if self.__match(keywords, self.p_prompts[x]['token']):
                weight = self.p_prompts[x]['weight'] if 'weight' in self.p_prompts[x] else 1
                r = inLoraRange if 'lora' in self.p_prompts[x] else inRange
                self.p_prompts[x]['weight'] = self.__modify_weight(weight, r, inMinOutput=0, inMaxOutput=inMaxOutput)
                self.__log_weight(self.p_prompts[x]['token'], weight, self.p_prompts[x]['weight'])

    def __match(self, inKeywords:list, inString:str):
        inString = inString.lower()
        for kw in inKeywords:
            if kw in inString:
                return True
        return False
    
    # def Shift(self, inList:list, inBefore:int, inAfter:int) -> list:
    #     return self.__shift(inList, inBefore, inAfter)
    
    def __shift(self, inList:list, inBefore:int, inAfter:int) -> list:
        if inBefore==inAfter:
            return inList
        newlist = []
        if inBefore<inAfter:
            newlist = inList[:inBefore]
            newlist += inList[inBefore+1:inAfter+1]
            newlist += inList[inBefore:inBefore+1]
            newlist += inList[inAfter+1:]
        else:
            newlist = inList[:inAfter]
            newlist += inList[inBefore:inBefore+1]
            newlist += inList[inAfter:inBefore]
            newlist += inList[inBefore+1:]

        return newlist

    def __modify_weight(self, inWeight:float, inRange:float, inMinInput:float=None, inMaxInput:float=None, inMinOutput:float=None, inMaxOutput:float=None):
        if (inMinInput is not None and inWeight<inMinInput) or (inMaxInput is not None and inWeight>inMaxInput):
            return inWeight

        mod = (self.rng.random() * inRange * 2)-inRange
        if inMinOutput is not None and (inWeight+mod) < inMinOutput:
            return inWeight
        if inMaxOutput is not None and (inWeight+mod) > inMaxOutput:
            return inWeight
        return inWeight+mod
    
    def __log_header(self, inHeader):
            self.p_log.append("= {header}".format(header=inHeader))

    def __log_entry(self, inPrompt, inEntry):
        self.p_log.append("{prompt}: {entry}".format(prompt=inPrompt, entry=inEntry))

    def __log_weight(self, inPrompt, inBefore, inAfter):
        # __modify_weight returns the weight untouched when the result would breach the
        # min/max bounds, so it is only a change if the value actually moved.  The entry
        # is still logged either way: a prompt that matched but held is worth seeing.
        if inAfter==inBefore:
            self.__log_entry(inPrompt, "Weight held at {before:0.2f} (change out of range)".format(before=inBefore))
        else:
            self.__log_entry(inPrompt, "Weight changed from {before:0.2f} to {after:0.2f}".format(before=inBefore, after=inAfter))

    def ScrambleReduction(self, inTarget:int, inRange:int=None, inKeepTokens:str=None):
        # target is number to eliminiate
        # range will randomize it as +/-
        # will not eliminate loras
        # will not eliminate tokens where there is a substring match on inKeepTokens
        if inTarget is None:
            return
            
        keep_tokens = []
        if inKeepTokens is not None:
            for tk in inKeepTokens.split(','):
                tk = tk.lower().strip()
                if tk!= "":
                    keep_tokens.append(tk)

        ln = len(self.p_prompts)

        pmap = []
        for x in range(ln):
            if 'lora' not in self.p_prompts[x]:
                pmap.append(x)

        self.rng.shuffle(pmap)

        if inRange is not None:
            inTarget += self.rng.randint(1, inRange*2) - inRange
        inTarget = min(max(inTarget, 1), len(pmap)-1)

        pmap = pmap[:inTarget]

        removed = []

        tks = []
        for x in range(ln):
            keep = False
            if x in pmap:
                for kt in keep_tokens:
                    if kt in self.p_prompts[x]['token'].lower():
                        keep = True
                        break
            if keep or x not in pmap:
                tks.append(self.p_prompts[x])
            else:
                removed.append(self.p_prompts[x]['token'])

        if len(removed)>0:
            self.__log_header("{target} prompts removed".format(target=len(removed)))
            for p in removed:
                self.__log_entry(p, "Removed")

        self.p_prompts = tks

    def Generate(self):
        self.__reset_generation()
        self.p_output = ""
        llen = 0
        for p in self.p_prompts:
            tk = p['token']
            weight = p['weight'] if 'weight' in p else None
            if 'lora' in p:
                if weight is not None and weight!=1:
                    tk += ":"+self.__format_weight(weight)
                tk = "<"+tk+">"
            elif weight is not None and weight!=1:
                # Always parenthesize.  Both ComfyUI and A1111 only read a weight that
                # sits inside parens -- a bare "token:1.2" is literal text, so the weight
                # is silently dropped and the ":1.2" is encoded as prompt content.  One
                # paren pair plus an explicit weight is exact and round-trips, so there
                # is no shorter form worth searching for.
                tk = "("+tk+":"+self.__format_weight(weight)+")"
            if llen>0:
                if llen+len(tk)>mPrompt.sLineSplit:
                    self.p_output += "\n"
                    llen = 0
                else:
                    self.p_output += ","
            self.p_output += tk
            llen += len(tk)
        return self.p_output

    def TestParse(self, inPrompt:str):
        self.__init_prompt(inPrompt)
        for prompt in self.p_prompts:
            print(prompt)

    def __format_weight(self, inWeight:float):
        # 3 decimals, trailing zeros trimmed.  Fixed-point rather than "{:.3}" so a very
        # small weight can never come out in exponent form, which no parser accepts.
        s = "{w:.3f}".format(w=inWeight).rstrip("0").rstrip(".")
        return s if s not in ("", "-") else "0"

    def __reset_generation(self):
        self.p_output = None

    def __init_prompt(self, inPrompt:str):
        self.p_string = inPrompt
        p = inPrompt.replace("\n", ",").replace("<", ",<").replace(">", ">,")
        lst = self.__split_prompts(p)
        tks = []
        for l in lst:
            tk = self.__make_token(l)
            if tk is not None:
                tks.append(tk)
        self.p_prompts = tks

    def __split_prompts(self, inString:str):
        # Split on commas that sit at bracket depth 0.  ( ) guards a weighted group;
        # [ ] and { } guard prompt-editing and wildcard constructs that other nodes
        # expand later -- a comma inside one of those belongs to the construct, not to
        # us, and splitting it leaves two halves that reorder independently into garbage.
        parts = []
        current = ""
        depth = 0
        escaped = False
        for ch in inString:
            if escaped:
                current += ch
                escaped = False
                continue
            if ch == "\\":
                current += ch
                escaped = True
                continue
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth = max(depth-1, 0)
            elif ch == "," and depth==0:
                parts.append(current)
                current = ""
                continue
            current += ch
        parts.append(current)
        return parts

    def __wraps_all(self, inString:str):
        # True when the paren that opens the string is the one that closes it, so the
        # parens really do enclose the whole phrase.
        depth = 0
        for i in range(len(inString)):
            if inString[i]=="(":
                depth += 1
            elif inString[i]==")":
                depth -= 1
                if depth==0:
                    return i==len(inString)-1
        return False

    def __make_token(self, inPrompt:str):
        inPrompt = inPrompt.strip()
        if inPrompt=="":
            return None
        inPrompt = inPrompt.replace("\\(", "@@@").replace("\\)", "###")
        # Peel only parens that wrap the entire phrase.  "(a, b) c" is not a weighted
        # group: stripping its parens would pull " c" inside and weight that too.
        pcnt = 0
        while len(inPrompt)>=2 and inPrompt[0]=="(" and inPrompt[-1]==")" and self.__wraps_all(inPrompt):
            inPrompt = inPrompt[1:-1].strip()
            pcnt += 1

        lcnt = inPrompt.count("<")
        inPrompt = inPrompt.replace("<", "").replace(">", "")

        # [ ] and { } belong to prompt-editing and wildcard processors that run outside
        # this node.  Their colons are syntax, not weights, so such a phrase is carried
        # through opaquely: it still reorders, but it is never re-weighted and never
        # re-parenthesized, either of which would corrupt it.
        opaque = lcnt==0 and any(ch in inPrompt for ch in "[]{}")

        weight = None
        if not opaque:
            pw = inPrompt.split(":")
            if len(pw)>1:
                try:
                    weight = (float)(pw[-1])
                    inPrompt = ":".join(pw[:len(pw)-1]).strip()
                except ValueError:
                    pass

        # Matches ComfyUI: a bare paren multiplies the weight by 1.1, while an explicit
        # ":w" replaces it outright rather than scaling it.
        if weight is None:
            weight = 1.1 ** pcnt

        if weight==0 or inPrompt=="":
            return None

        inPrompt = inPrompt.replace("@@@", "\\(").replace("###", "\\)")
        
        tk = {'token':inPrompt}
        if weight is not None and weight!=1:
            tk['weight'] = weight
        if lcnt>0:
            tk['lora'] = True
        if opaque:
            tk['opaque'] = True

        return tk
