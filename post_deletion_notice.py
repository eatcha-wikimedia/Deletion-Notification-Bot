import os
import csv
import pywikibot
from datetime import datetime, timedelta
from pywikibot import pagegenerators, logentries
from pathlib import Path
today = datetime.utcnow()

post_del_file = ".logs/post_deletion_%s.csv" % today.strftime("%B_%Y")

class DeletedFile:
    def __init__(self, file_name):
        self.file_name = file_name
    
    def deleter_admin(self):
        for log in pywikibot.site.APISite.logevents(SITE,logtype="delete",page=self.file_name):
            return log.data.get("user")
    
    def delete_comment(self):
        for log in pywikibot.site.APISite.logevents(SITE,logtype="delete",page=self.file_name):
            return log.data.get("comment")

    def uploader(self):
        try:
            return([info for info in pywikibot.site.APISite.logevents(SITE,logtype="upload",page=self.file_name,reverse=True,total=1)])[0].user()
        except:
            return "Unknown"

    def uploader_rights_list(self):
        return pywikibot.User(SITE, self.uploader()).groups(force=True)

    def uploader_talk_page(self):
        user = pywikibot.User(SITE, self.uploader())
        uploader_talk_page = user.getUserTalkPage()
        if uploader_talk_page.isRedirectPage():
            uploader_talk_page = uploader_talk_page.getRedirectTarget()
        return uploader_talk_page

    def is_aware(self):
        if self.file_name in self.uploader_talk_page().get():return "Yes"
        else:return "No"

    def log_it(self):
        if not os.path.isfile(post_del_file):open(post_del_file, 'w').close()
        with open(post_del_file,'a') as fd:
            NewFileRow = "\n{ca}, {cb}, {cc}, {cd}".format(ca=self.is_aware(),cb=self.file_name,cc=self.uploader(),cd=self.deleter_admin())
            fd.write(NewFileRow)

    def out_file_info(self):
        out("Name : %s" % self.file_name, color = "yellow")
        out("Uploader : %s" % self.uploader(), color = "yellow")
        out("Deleted by : %s" % self.deleter_admin(), color = "yellow")
        out("Delete reason : %s" % self.delete_comment(), color = "yellow")
        out("\n\n")

    def notify_uploader(self):
        old_text = self.uploader_talk_page().get()
        reason, admin = self.delete_comment(), self.deleter_admin()
        new_text = ( old_text + "\n{{subst:User:Deletion Notification Bot/deleted notice|1=%s}}Deleted by [[User:%s]]. Reason for deletion : %s . \n~~~~" % (self.file_name, admin, reason))
        summary = "[[%s]] was recently deleted by %s " % (self.file_name, admin)
        commit(old_text, new_text, self.uploader_talk_page(), summary)

def logged_data():
    try:
        with open(post_del_file, "r") as f:
            post_del_data = f.read()
    except:post_del_data = ""
    Path(".logs").mkdir(parents=True, exist_ok=True)
    m_log = ".logs/%s.csv" % today.strftime("%B_%Y")
    if not os.path.isfile(m_log):open(m_log, 'w').close()
    with open(m_log, "r") as f:
        stored_data = f.read()
    return (post_del_data + "\n" + stored_data)

def Notify():
    gen  = pagegenerators.LogeventsPageGenerator(
        logtype = "delete",
        site = SITE,namespace = 6,
        start = pywikibot.site.APISite.getcurrenttimestamp(SITE),
        end = (
            today-timedelta(days=1)
        ).strftime("%Y%m%d%H%M%S")
    )
    logged_files = logged_data()

    for deleted_file in gen:
        file_obj = DeletedFile(deleted_file.title())
        if file_obj.file_name in logged_files:
            continue
        else:
            file_obj.log_it()
        try:
            pywikibot.Page(SITE, file_obj.file_name).get(get_redirect=True, force=True)
            continue
        except:
            Uploader = file_obj.uploader()
            if Uploader == "Unknown":
                continue
            if 'bot' in file_obj.uploader_rights_list() or 'bot' in Uploader.lower():
                out("We don't want the bot to notify another bot", color="white")
                continue
            file_obj.out_file_info()
            if file_obj.is_aware() == "No":
                file_obj.notify_uploader()
            else:
                continue

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

def main():
    global SITE
    SITE = pywikibot.Site()
    Notify()

if __name__ == "__main__":
  try:
    main()
  finally:
    pywikibot.stopme()
