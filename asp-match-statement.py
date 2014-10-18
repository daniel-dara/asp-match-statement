# TODO:
# Add logic for comments
# Add logic for cases like this:
#   If condition = "If Then" Then
#   End If

import sublime
import sublime_plugin
import re

class MatchStatementCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print("running plugin...")

        # Get environment variables.
        view = self.view # sublime.View
        sel = view.sel() # sublime.Selection

        # Get the first region of the selection (other selected regions are ignored).
        region = view.sel()[0] # sublime.Region

        # Store the whole document in a string.
        document = view.substr(sublime.Region(0, view.size()))

        # If there is no selection, then select the line the cursor is currently on.
        if region.a == region.b:
            region = view.line(region)

        # Get the selected text.
        selectedText = view.substr(region)
        
        # Turn off case sensitivity and detect keywords split across multiple lines (such as If... Then)
        regexFlags   = re.I | re.S

        # Initialize regular expression patterns
        regexNonAsp     = r"%>((?!<%).)*<%"
        regexString     = r"\"[^\"]*\""
        
        regexNonAspRev  = r"%<((?!>%).)*>%"
        
        regexIfThen     = r"\bIf((?!\bThen\b).)*Then\b"
        regexEndIf      = r"\bEnd\s*If\b"
        
        regexIfThenRev  = r"\bnehT((?!\bfI\b).)*fI\b"
        regexEndIfRev   = r"\bfI\s*dnE\b"
        
        regexDoWhile    = r"\bDo\s*While\b"
        regexLoop       = r"\bLoop\b"
        
        regexDoWhileRev = r"[^:\n]*\s*elihW\s*oD\b"
        regexLoopRev    = r"\bpooL\b"

        regexSub        = r"(^|:|\n)\s*(Private|Public)?\s*Sub\s*[^$:\n]*"
        regexEndSub     = r"\bEnd\s*Sub\b"

        regexSubRev     = r"[^:^\n]*[\t ]+buS([\t ]+(etavirP|cilbuP))?"
        regexEndSubRev  = r"\bbuS\s+dnE\b"

        # Remove string literals and non-ASP code from the selection so there are no
        # false-positive matches.
        selectedText = re.sub(regexString, "", selectedText, regexFlags)
        selectedText = re.sub(regexNonAsp, "", selectedText, regexFlags)

        # Initialize statement configurations
        statementConfigurations = [
            ("If Then", regexIfThen, regexIfThen, regexEndIf, False),
            ("End If", regexEndIf, regexEndIfRev, regexIfThenRev, True),
            ("Do While", regexDoWhile, regexDoWhile, regexLoop, False),
            ("Loop", regexLoop, regexLoopRev, regexDoWhileRev, True),
            ("End Sub", regexEndSub, regexEndSubRev, regexSubRev, True),
            ("Sub", regexSub, regexSub, regexEndSub, False),
            ]

        statementType = None

        # Detect what type of statement was selected and what will be searched for
        for config in statementConfigurations:
            if re.search(config[1], selectedText, regexFlags):
                statementType = config[0]
                print("Found statement of type: " + statementType)
                statementStart = config[2]
                statementEnd = config[3]
                isReverse = config[4]
                break

        if statementType is None:
            print("No keywords specified. Exiting.")
            return

        if isReverse:
            regexNonAsp = regexNonAspRev
            cursorIndex = view.size() - min(region.a, region.b) # reverse the cursor index
            document = document[::-1] # reverse the document
        else:
            cursorIndex = max(region.a, region.b)

        # Initialize other local variables
        matchStatementEnd = 0 # kick start the loop
        nestingLevel      = 0

        while True:
            matchStatementEnd   = re.compile(statementEnd, regexFlags).search(document, cursorIndex)
            matchStatementStart = re.compile(statementStart, regexFlags).search(document, cursorIndex)
            matchString         = re.compile(regexString, regexFlags).search(document, cursorIndex)
            matchNonAsp         = re.compile(regexNonAsp, regexFlags).search(document, cursorIndex)

            #print("matchStatementEnd: " + str(matchStatementEnd.start()))
            #print("matchString: " + str(matchString.start()))
            #print("matchNonAsp: " + str(matchNonAsp.start()))

            # "Statement End" is considered to be the statement we are looking for, regardless if it is
            # actually the end of a statement or not.
            if matchStatementEnd is None:
                print("No ending statement found.")
                return

            matches = [(matchStatementEnd.start(), matchStatementEnd)]

            if matchString is not None:
                matches.append((matchString.start(), matchString))

            if matchNonAsp is not None:
                matches.append((matchNonAsp.start(), matchNonAsp))

            if matchStatementStart is not None:
                matches.append((matchStatementStart.start(), matchStatementStart))

            closest = min(matches, key=lambda x: x[0])[1]
            # closest = min(matches, key=lambda x: x.start())

            if closest == matchStatementEnd:
                if nestingLevel == 0:
                    print("Found the statements pair!")

                    sel.clear()

                    start = closest.start()
                    end = closest.end()

                    if isReverse:
                        start = view.size() - start
                        end = view.size() - end

                    # select the entire statement
                    sel.add(sublime.Region(start, end))

                    # scroll to the selection if it is currently off screen
                    view.show(sel)
                    return
                else:
                    nestingLevel -= 1
            elif closest == matchStatementStart:
                print("nesting plus one")
                nestingLevel += 1

            cursorIndex = closest.end()