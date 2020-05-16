import os
import csv
import pywikibot
from datetime import datetime, timedelta
from pywikibot import pagegenerators, logentries
from pathlib import Path
today = datetime.utcnow()

post_del_file = ".logs/post_deletion_%s.csv" % today.strftime("%B_%Y")

def Log_info(IsAware, FileName,UploaderName):
    if not os.path.isfile(post_del_file):open(post_del_file, 'w').close()
    with open(post_del_file,'a') as fd:
        NewFileRow = "\n{c_a}, {c_b}, {c_c}".format(c_a=IsAware,c_b=FileName,c_c=UploaderName)
        fd.write(NewFileRow)

def AwarenessCheck(FileName,UploaderTalkPage):
    if FileName in UploaderTalkPage.get():return "Yes"
    else:return "No"

def uploader(FileName):
    return([info for info in pywikibot.site.APISite.logevents(SITE,logtype="upload",page=FileName,reverse=True,total=1)])[0].user()

def commit(old_text, new_text, page, summary):
    out("\nAbout to make changes at : '%s'" % page.title())
    pywikibot.showDiff(old_text, new_text)
    #page.put(new_text, summary=summary, watchArticle=True, minorEdit=False)

def out(text, newline=True, date=False, color=None):
    if color:
        text = "\03{%s}%s\03{default}" % (color, text)
    dstr = (
        "%s: " % datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if date
        else ""
    )
    pywikibot.stdout("%s%s" % (dstr, text), newline=newline)

def deletion_info(FileName):
    for log in pywikibot.site.APISite.logevents(SITE,logtype="delete",page=FileName):
        reason = log.data.get("comment")
        admin = log.data.get("user")
    return reason, admin

def post_data():
    try:
        with open(post_del_file, "r") as f:
            post_del_data = f.read()
    except:
        post_del_data = ""
    
    return post_del_data

def Notify():
    gen  = pagegenerators.LogeventsPageGenerator(
        logtype = "delete",
        site = SITE,
        namespace = 6,
        start = pywikibot.site.APISite.getcurrenttimestamp(SITE),
        end = (today-timedelta(days=1)).strftime("%Y%m%d%H%M%S"),
        )
    post_del_data = post_data()
    Path(".logs").mkdir(parents=True, exist_ok=True)
    m_log = ".logs/%s.csv" % today.strftime("%B_%Y")
    if not os.path.isfile(m_log):open(m_log, 'w').close()
    with open(m_log, "r") as f:
        stored_data = f.read()

    for deleted_file in gen:
        FileName = deleted_file.title()

        if FileName in (stored_data + "\n" + post_del_data):
            out("%s was processed by the pre script." % FileName, color="white")
            continue
        
        try:
            old_text = pywikibot.Page(SITE, FileName).get(get_redirect=True, force=True)
            continue
        except:
            pass

            try:
                Uploader = uploader(FileName)
            except IndexError:
                continue

            rights_array = pywikibot.User(SITE,Uploader).groups(force=True)
            if 'bot' in rights_array or 'bot' in Uploader.lower():
                out("We don't want the bot to notify another bot", color="white")
                continue
            user = pywikibot.User(SITE, Uploader)
            uploader_talk_page = user.getUserTalkPage()
            if uploader_talk_page.isRedirectPage():
                uploader_talk_page = uploader_talk_page.getRedirectTarget()
            IsAware = AwarenessCheck(FileName,uploader_talk_page)
            Log_info(IsAware,user.title(),FileName,)
            out("""%s is deleted, it was uploaded by %s and they were %s of it's Deletion.""" % (FileName,user.title(), ("aware" if IsAware == "Yes" else "not aware")),)
            if IsAware == "No":
                old_text = uploader_talk_page.get()
                reason, admin = deletion_info(FileName)
                new_text = ( old_text + "\n{{subst:User:Deletion Notification Bot/deleted notice|1=%s}}Deleted by [[User:%s]]. Reason for deletion : %s . \n~~~~" % (FileName, admin, reason))
                summary = "Notify user about deletion of [[%s]]" % FileName
                commit(old_text, new_text, user.getUserTalkPage(), summary)
            else:
                continue
def main():
    global SITE
    SITE = pywikibot.Site()
    Notify()
    

if __name__ == "__main__":
  try:
    main()
  finally:
    pywikibot.stopme()
