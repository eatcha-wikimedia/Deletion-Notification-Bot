import os
import csv
import urllib3
import json
import pywikibot
from datetime import datetime, timedelta
from pywikibot import pagegenerators, logentries
from pathlib import Path

today = datetime.utcnow()
post_del_file = ".logs/post_deletion_%s.csv" % today.strftime("%B_%Y")
last_100_users = []

class DeletedFile:
    def __init__(self, file_name):
        self.file_name = file_name
    
    def deleter_admin(self):
        for log in pywikibot.site.APISite.logevents(SITE,logtype="delete",page=self.file_name):
            return log.data.get("user")
    
    def delete_comment(self):
        for log in pywikibot.site.APISite.logevents(SITE,logtype="delete",page=self.file_name):
            return log.data.get("comment")

    def is_locked(self):
        http = urllib3.PoolManager()
        r = http.request('GET', 'https://login.wikimedia.org/w/api.php?action=query&meta=globaluserinfo&format=json&guiuser=%s' % self.uploader())
        data = json.loads(r.data.decode('utf-8'))
        if (data.get("query").get("globaluserinfo").get("locked", False)) is False:
            return False
        return True

    def uploader(self):
        try:
            return([info for info in pywikibot.site.APISite.logevents(SITE,logtype="upload",page=self.file_name,reverse=True,total=1)])[0].user()
        except:
            return "Unknown"

    @property
    def uploader_ec(self):
        user = pywikibot.User(SITE, self.uploader())
        return user.editCount(force=True)

    def uploader_rights_list(self):
        return pywikibot.User(SITE, self.uploader()).groups(force=True)

    def uploader_talk_page(self):
        user = pywikibot.User(SITE, self.uploader())
        uploader_talk_page = user.getUserTalkPage()
        if uploader_talk_page.isRedirectPage():
            uploader_talk_page = uploader_talk_page.getRedirectTarget()
        return uploader_talk_page

    def subpage_editors(self):
        subpage = "Commons:Deletion requests/%s" % self.file_name
        page = pywikibot.Page(SITE, subpage)
        hist = page.revisions()
        editors = []
        for d in hist:
            editors.append(d.user)
        return editors

    def is_aware(self):
        try:
            subpage_users = self.subpage_editors()
        except pywikibot.exceptions.NoPage:
            subpage_users = []
        global last_100_users
        if len(last_100_users) > 100:
            last_100_users = []
        else:
            last_100_users.append(self.uploader())
            count_of_this_uploader = last_100_users.count(self.uploader())
            if count_of_this_uploader > 3:
                return "Yes"

        self_del_list = [
            "author's request",
            "uploader request",
            "author request",
            "G7",
            "user request",
            "roken redirect", #works as [Bb]
            "#REDIRECT",
        ]

        if self.uploader_ec > 5000:
            return "Yes"

        elif any(s in self.delete_comment() for s in self_del_list):
            return "Yes"

        elif self.uploader() == self.deleter_admin():
            return "Yes"

        elif self.uploader() in subpage_users:
            return "Yes"

        elif self.file_name in self.uploader_talk_page().get():
            return "Yes"

        else:
            return "No"

    def log_it(self):
        if not os.path.isfile(post_del_file):open(post_del_file, 'w').close()
        with open(post_del_file,'a') as fd:
            NewFileRow = "\n{ca}, {cb}, {cc}".format(ca=self.file_name,cb=self.uploader(),cc=self.deleter_admin())
            fd.write(NewFileRow)

    def out_file_info(self):
        out("Name : %s" % self.file_name, color = "yellow")
        out("Uploader : %s" % self.uploader(), color = "yellow")
        out("Deleted by : %s" % self.deleter_admin(), color = "yellow")
        out("Delete reason : %s" % self.delete_comment(), color = "yellow")
        out("Uploader ec : %d" % self.uploader_ec, color = "yellow")

    def notify_uploader(self):
        old_text = self.uploader_talk_page().get()
        reason, admin = self.delete_comment(), self.deleter_admin()
        new_text = ( old_text + "\n{{subst:User:Deletion Notification Bot/deleted notice|1=%s}}Deleted by [https://commons.wikimedia.org/wiki/User:%s User:%s]. Reason for deletion : %s . \n~~~~" % (self.file_name, admin.replace(" ", "_"), admin, reason))
        summary = "[[%s]] was recently deleted by User:%s " % (self.file_name, admin)
        commit(old_text, new_text, self.uploader_talk_page(), summary)

    def handle(self, logged_files):
        try:
            pywikibot.Page(SITE, self.file_name).get(get_redirect=True, force=True)
            return
        except:
            Uploader = self.uploader()
            if Uploader == "Unknown":
                return

            if self.file_name in logged_files:
                return
            else:
                self.log_it()


            self.out_file_info()

            if 'bot' in self.uploader_rights_list() or 'bot' in Uploader.lower():
                out("We don't want the bot to notify another bot", color="white")
                return

            if self.is_locked():
                out("Uploader is global locked")
                return

            if pywikibot.User(SITE, Uploader).isBlocked(force=True):
                out("uploader %s is banned." % Uploader, color="white")
                return

            if self.is_aware() == "No":
                self.notify_uploader()
            else:
                out("uploader aware of the file\n\n")
                return

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

def commit(old_text, new_text, page, summary):
    out("\nAbout to make changes at : '%s'" % page.title())
    pywikibot.showDiff(old_text, new_text)
    summary = summary + ".  [[Commons:Bots/Requests/Deletion Notification Bot| Report Bugs / Suggest improvements]] (trial run)"
    page.put(new_text, summary=summary, watchArticle=True, minorEdit=False)

def out(text, newline=True, date=False, color=None):
    if color:
        text = "\03{%s}%s\03{default}" % (color, text)
    dstr = (
        "%s: " % datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if date
        else ""
    )
    pywikibot.stdout("%s%s" % (dstr, text), newline=newline)

def main(*args):
    global SITE
    args = pywikibot.handle_args(*args)
    SITE = pywikibot.Site()
    if not SITE.logged_in():
        SITE.login()
    gen  = pagegenerators.LogeventsPageGenerator(
        logtype = "delete",
        site = SITE,namespace = 6,
        start = pywikibot.site.APISite.getcurrenttimestamp(SITE),
        end = (today-timedelta(hours=2)).strftime("%Y%m%d%H%M%S")
    )
    logged_files = logged_data()
    for deleted_file in gen:
        DeletedFile(deleted_file.title()).handle(logged_files)


if __name__ == "__main__":
  try:
    main()
  finally:
    pywikibot.stopme()
