import pywikibot
from pywikibot import pagegenerators
from datetime import datetime

today = datetime.utcnow()

def AwarenessCheck(FileName,UploaderTalkPage):
    if FileName in UploaderTalkPage.get():
        return "Yes"
    else:
        return "No"

def commit(old_text, new_text, page, summary):
    """Show diff and submit text to page."""
    out("\nAbout to make changes at : '%s'" % page.title())
    pywikibot.showDiff(old_text, new_text)
    #page.put(new_text, summary=summary, watchArticle=True, minorEdit=False)

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

def uploader(file_name, link=True):
    """Return the link to the user that uploaded this file"""
    history = pywikibot.Page(SITE,file_name).getVersionHistory(reverseOrder=True, total=1)
    if not history:
        return "Unknown"
    if link:
        return "[[User:%s|%s]]" % (history[0][2], history[0][2])
    else:
        return history[0][2]

def Notify(cat):
    gen = pagegenerators.CategorizedPageGenerator(pywikibot.Category(SITE,cat))
    for page in gen:
        file_name = page.title()
        if file_name.startswith("File:"):
            uploader_talk = pywikibot.User(SITE, uploader(file_name, link=False)).getUserTalkPage().get()
            if file_name in uploader_talk:
                continue
            print(file_name)
            print(uploader(file_name, link=False))

            # these are SDs (deleted within 2 days or less)
            dict = {
                "Advertisements for speedy deletion": "{{subst:User:Deletion Notification Bot/NOADS|1=%s}}" % file_name,
                "Copyright violations": "{{subst:copyvionote|1=%s}}" % file_name,
                "Other speedy deletions": "{{subst:User:Deletion Notification Bot/SDEL|1=%s}}" % file_name,
                "Personal files for speedy deletion": "{{subst:User:Deletion Notification Bot/personalNO|1=%s}}" % file_name,
                "Deletion requests %s" % today.strftime("%B %Y") : "{{subst:idw|1=%s}}" % file_name,
                "Media without a license as of %s" % today.strftime("%-d %B %Y") : "{{subst:image license|1=%s}}" % file_name,
                "Media missing permission as of %s" % today.strftime("%-d %B %Y") : "{{subst:image permission|1=%s}}" % file_name,
                "Media without a source as of %s" % today.strftime("%-d %B %Y") : "{{subst:Image source |1=%s}}" % file_name,

            }
            print(dict.get(cat))

            if cat in ['Advertisements for speedy deletion', 'Copyright violations', 'Other speedy deletions', 'Personal files for speedy deletion']:
                pass
                

            # Deleted in 7 days
            elif cat in ['Media without a license as of 25 March 2020', 'Media missing permission as of 25 March 2020', 'Media without a source as of 25 March 2020']:
                pass
                

            # these are normal DRs : Media without a license as of dd month yyyy
            else:
                pass
                

    
def main(*args):
    global SITE
    args = pywikibot.handle_args(*args)
    SITE = pywikibot.Site()


    Deletion_Cats = [
        "Advertisements for speedy deletion",                  #0
        "Copyright violations",                                #1
        "Other speedy deletions",                              #2
        "Personal files for speedy deletion",                  #3
        "Deletion requests %s" % today.strftime("%B %Y"),                        #4
        "Media without a license as of %s" % today.strftime("%-d %B %Y"),         #5
        "Media missing permission as of %s" % today.strftime("%-d %B %Y"),        #6
        "Media without a source as of %s" % today.strftime("%-d %B %Y"),          #7
        ]

    for cat in Deletion_Cats:
        Notify(cat)
        

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
