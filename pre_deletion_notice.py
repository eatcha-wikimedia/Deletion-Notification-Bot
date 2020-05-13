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

def last_editor(filename, link=True):
    """User that uploaded the file."""
    history = (pywikibot.Page(SITE, filename)).revisions(reverse=False, total=1)
    for info in history:
        username = (info.user)
    if not history:
        return "Unknown"
    if link:
        return "[[User:%s|%s]]" % (username, username)
    return username

def uploader(filename, link=True):
    """User that uploaded the file."""
    history = (pywikibot.Page(SITE, filename)).revisions(reverse=True, total=1)
    for info in history:
        username = (info.user)
    if not history:
        return "Unknown"
    if link:
        return "[[User:%s|%s]]" % (username, username)
    return username

def Notify(cat):
    gen = pagegenerators.CategorizedPageGenerator(pywikibot.Category(SITE,cat))
    for page in gen:
        file_name = page.title()
        if file_name.startswith("File:"):

            Uploader = uploader(file_name, link=False)

            if Uploader == last_editor(file_name, link=False):
                out("We don't want the bot to notify if Uploader asked for deletion", color="white")
                continue

            rights_array = pywikibot.User(SITE, Uploader).groups(force=True)

            if 'bot' in rights_array or 'bot' in Uploader.lower():
                out("We don't want the bot to notify another bot", color="white")
                continue

            uploader_talk_page = pywikibot.User(SITE, Uploader).getUserTalkPage()
            uploader_talk_text = uploader_talk_page.get()

            if file_name in uploader_talk_text:
                continue

            print(file_name)
            print(uploader(file_name, link=False))
            # these are SDs (deleted within 2 days)
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
            message = ( "\n" + dict.get(cat) + "\nI am a software, please do not ask me any questions but at the [https://commons.wikimedia.org/wiki/Commons:Help_desk help desk]. //~~~~" )
            new_text = uploader_talk_text + message
            summary = "Notification of [[Category:%s|%s]] - [[:%s]]" % (cat,cat,file_name)
            try:
                commit(uploader_talk_text, new_text, uploader_talk_page, summary)
            except:
                pass

def main(*args):
    global SITE
    args = pywikibot.handle_args(*args)
    SITE = pywikibot.Site()
    if not SITE.logged_in():
        SITE.login()

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
