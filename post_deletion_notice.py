import os
import csv
import pywikibot
from datetime import datetime,timedelta
from pywikibot import pagegenerators, logentries

CSV_file = os.path.dirname(os.path.realpath(__file__)) + "/deletion_data.csv"

def Log_info(IsAware, FileName,UploaderName):
  with open(CSV_file,'a') as fd:
    NewFileRow = "\n{c_a}, {c_b}, {c_c}".format(c_a=IsAware,c_b=FileName,c_c=UploaderName)
    fd.write(NewFileRow)

def AwarenessCheck(FileName,UploaderTalkPage):
    if FileName in UploaderTalkPage.get():
        return "Yes"
    else:
        return "No"

def commit(old_text, new_text, page, summary):
    """Show diff and submit text to page."""
    out("\nAbout to make changes at : '%s'" % page.title())
    pywikibot.showDiff(old_text, new_text)
    page.put(new_text, summary=summary, watchArticle=True, minorEdit=False)

def out(text, newline=True, date=False, color=None):
    """Just output some text to the consoloe or log."""
    if color:
        text = "\03{%s}%s\03{default}" % (color, text)
    dstr = (
        "%s: " % datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if date
        else ""
    )
    pywikibot.stdout("%s%s" % (dstr, text), newline=newline)

def get_delete_reason(FileName):
    reason = "No reason found"
    logevents = pywikibot.site.APISite.logevents(
        SITE,
        logtype = "delete",
        page = FileName,
        reverse = True,
        )
    for log in logevents:
        reason = log.comment()
    return reason

def Notify():
    gen  = pagegenerators.LogeventsPageGenerator(
        logtype = "delete",
        site = SITE,
        namespace = 6,
        )
    for deleted_file in gen:
        FileName = deleted_file.title()
        try:
            old_text = pywikibot.Page(SITE, FileName).get(get_redirect=True, force=True)
            continue
        except:
            pass
        logevents = pywikibot.site.APISite.logevents(
            SITE,
            logtype = "upload",
            page = FileName,
            reverse = True,
            )
        for log in logevents:
            user = pywikibot.User(SITE, log.user())
            IsAware = AwarenessCheck(FileName,user.getUserTalkPage())
            Log_info(IsAware,user.title(),FileName,)
            out("""%s is deleted, it was uploaded by %s and they were %s of it's Deletion.""" % (FileName,user.title(), ("aware" if IsAware == "Yes" else "not aware")),)
            if IsAware == "No":
                old_text = user.getUserTalkPage().get()
                new_text = ( old_text + "\n{{subst:User:Deletion Notification Bot/deleted notice|1=%s}}Reason for deletion : %s \n~~~~" % (FileName, get_delete_reason(FileName)))
                summary = "Notify user about deletion of [[%s]]" % FileName
                commit(old_text, new_text, user.getUserTalkPage(), summary)
def main():
    global SITE
    SITE = pywikibot.Site()
    Notify()
    

if __name__ == "__main__":
  try:
    main()
  finally:
    pywikibot.stopme()
