import pywikibot
from pywikibot import pagegenerators
from datetime import datetime
import re
from pathlib import Path
import csv
import os
import requests
from requests.exceptions import HTTPError
import json

today = datetime.utcnow()

def commit(old_text, new_text, page, summary):
    """Show diff and submit text to page."""
    out("\nAbout to make changes at : '%s'" % page.title())
    pywikibot.showDiff(old_text, new_text)
    summary = summary + ".  [[Commons:Bots/Requests/Deletion Notification Bot| Report Bugs / Suggest improvements]] (trial run)"
    page.put(new_text, summary=summary, watchArticle=True, minorEdit=False)

def is_locked(user):
    headers = {'user-agent': 'User:Deletion Notification Bot @ wikimedia Commons'}
    try:
        response = requests.get('https://login.wikimedia.org/w/api.php?action=query&meta=globaluserinfo&format=json&guiuser=%s' % user, headers=headers)
    except HTTPError as http_err:
        print('HTTP error occurred: %s' % http_err)
    except Exception as err:
        print('Other error occurred: %s' % err)

    if response.ok:
        data = response.json()
        if (data.get("query").get("globaluserinfo").get("locked", False)) is False:
            return False
        else:
            return True
    else:
        return True


def recent_editor(file_name):
    """Recent most editor for file."""
    history = (pywikibot.Page(SITE, file_name)).revisions(reverse=False, total=1)
    for data in history:
        username = (data.user)
    if not history:
        return "Unknown"
    return username

def out(text, newline=True, date=False, color=None):
    """output some text to the consoloe / log."""
    if color:
        text = "\03{%s}%s\03{default}" % (color, text)
    dstr = (
        "%s: " % datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if date
        else ""
    )
    pywikibot.stdout("%s%s" % (dstr, text), newline=newline)

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

def find_subpage(file_name):
    page_text = pywikibot.Page(SITE, file_name).get()
    try:
        subpage = re.search(r"\|subpage=(.*?)\|year", page_text).group(1)
    except AttributeError:
        subpage = file_name
    return subpage.strip()

def storeData(file_name, Uploader, cat, nominator, m_log):
    with open(m_log, mode='a') as data_file:
        writer = csv.writer(data_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([file_name, Uploader, cat, nominator])

def Nominator(file_name, cat, subpage=None):

    def del_nominator(filename):
        history = (pywikibot.Page(SITE, filename)).revisions(content=True, reverse=True)
        for data in history:
            content = data['slots']['main']['*']
            comment = data.comment
            user = data.user
            text_to_search = (comment + "\n" + content).lower()
    
            key_words = [
                'delet',
                'copyvio',
                'speedydelete',
                '{{sd',
                'no license since',
                'unfree flickr',
                'missing permission',
                'dw no source',
                'no permission since',
                '{{speedy',
                'no source since',
                '{{db-f9',
                '{{logo}}',
                
            ]
            if any(word in text_to_search for word in key_words):
                break
            else:
                comment=user=content =" "
        return comment, user, content

    del_comment, del_user, del_content =  del_nominator(file_name)
    if not del_user.isspace():
        return del_user

    elif cat == "Deletion requests %s" % today.strftime("%B %Y"):
        page_name = "Commons:Deletion_requests/" + subpage
        try:
            nr = uploader(page_name, link=False)
        except:
            nr = "Unknown"
        return nr
    else:
        return None

def get_copyvio_reason(file_name):
    text = pywikibot.Page(SITE, file_name).get()
    match = re.search(r"{{(?:\s*?|)[Cc]opyvio(?:\s*?|)\|(.*?)}}", text)
    if match:
        reason=match.group(1).replace("1=", " ").replace("|", " ")
    else:
        if re.search(r"{{(?:\s*?|)logo(.*?)}}", text):
            reason = "File is a non free logo"
        else:
             reason = ""
    return reason

def get_other_speedy_reason(file_name):
    text = pywikibot.Page(SITE, file_name).get()
    match = re.search(r"{{(?:\s*?|)(?:[Ss]peedy|[Ss]peedy\s*?[Dd]elete)(?:\s*?|)\|(.*?)}}", text)
    if match:
        reason=match.group(1).replace("1=", " ").replace("|", " ")
    else:
        reason = ""
    return reason
        
g_file_count = 0
def Notify(cat):
    gen = pagegenerators.CategorizedPageGenerator(pywikibot.Category(SITE, cat))
    uploader_and_uploads = {}
    for page in gen:
        file_name = page.title()
        if file_name.startswith("File:"):

            Uploader = uploader(file_name, link=False)
            
            if uploader_and_uploads.get(Uploader):
                files_list = uploader_and_uploads.get(Uploader)
                files_list.append(file_name)
                uploader_and_uploads[Uploader] = files_list
            else:
                uploader_and_uploads[Uploader] = [file_name]
    
    for Uploader, files_list in uploader_and_uploads.items():
        new_text = ""
        uploader_talk_page = pywikibot.User(SITE, Uploader).getUserTalkPage()
        if uploader_talk_page.isRedirectPage():
            uploader_talk_page = uploader_talk_page.getRedirectTarget()
        uploader_talk_text = uploader_talk_page.get()

        file_count = 0
        for file_name in files_list:
            global  g_file_count
            g_file_count += 1

            if cat == "Deletion requests %s" % today.strftime("%B %Y"):
                subpage = find_subpage(file_name)
                nominator = Nominator(file_name, cat, subpage=subpage)
                if subpage in uploader_talk_text:
                    _is_aware = True
            else:
                nominator = Nominator(file_name, cat)

            out("\n\n %d\n %s\n Uploaded by User:%s\n nominated by User:%s" % (g_file_count, file_name, Uploader, nominator) , color="yellow")

            Path(".logs").mkdir(parents=True, exist_ok=True)
            m_log = ".logs/%s.csv" % today.strftime("%B_%Y")
            if not os.path.isfile(m_log):open(m_log, 'w').close()
            with open(m_log, "r") as f:
                stored_data = f.read()

            if file_name in stored_data:
                out("%s was processed once." % file_name, color="white")
                continue

            storeData(file_name, Uploader, cat, nominator, m_log)
            
            if cat == "Deletion requests %s" % today.strftime("%B %Y"):
                if _is_aware:
                    out("Aware of DR, subpage found on uploader talk page.", color="white")
                    continue

            if nominator == "AntiCompositeBot":
                out("AntiCompositeBot's task")
                continue

            if pywikibot.User(SITE, Uploader).isBlocked(force=True) or is_locked(Uploader):
                out("uploader %s is locked/blocked." % Uploader, color="white")
                continue

            if "moved page" in (next((pywikibot.Page(SITE, file_name)).revisions(reverse=True,total =1)).comment):
                out("%s is just a redirect." % file_name, color="white")
                continue

            if Uploader == recent_editor(file_name):
                out("Uploader %s , is the last editor" % Uploader, color="white")
                continue

            if Uploader == nominator:
                out("Uploader %s is the nominatortor himself." % Uploader, color="white")
                continue

            rights_array = pywikibot.User(SITE, Uploader).groups(force=True)

            if 'bot' in rights_array or 'bot' in Uploader.lower():
                out("Uploader %s is a robot." % Uploader, color="white")
                continue

            if file_name.replace("File:", "") in uploader_talk_text:
                out("%s knows about deletion of %s . " % (Uploader, file_name) , color="white")
                continue

            dict = {
                "Advertisements for speedy deletion": "{{subst:User:Deletion Notification Bot/NOADS|1=%s}}" % file_name,
                "Copyright violations": "{{subst:copyvionote|1=%s|2=}}" % file_name,
                "Other speedy deletions": "{{subst:User:Deletion Notification Bot/SDEL|1=%s|2=}}" % file_name,
                "Personal files for speedy deletion": "{{subst:User:Deletion Notification Bot/personalNO|1=%s}}" % file_name,
                "Deletion requests %s" % today.strftime("%B %Y") : "{{subst:idw|1=%s|2=}}" % file_name,
                "Media without a license as of %s" % today.strftime("%-d %B %Y") : "{{subst:image license|1=%s}}" % file_name,
                "Media missing permission as of %s" % today.strftime("%-d %B %Y") : "{{subst:image permission|1=%s}}" % file_name,
                "Media without a source as of %s" % today.strftime("%-d %B %Y") : "{{subst:Image source |1=%s}}" % file_name,
            }
            
            file_count += 1

            if file_count <= 1:
                if nominator:
                    nominator_details = """<p style="font-size:0.8em;font-family:'Stencil Std'">\nUser who nominated the file for deletion (Nominator) : {{Noping|%s}}.</p>""" % nominator
                else:
                    nominator_details = ""
                message = ("\n" + dict.get(cat) + nominator_details)

                if cat == "Deletion requests %s" % today.strftime("%B %Y"):
                    message = message.replace("|2=", "|2=%s" % subpage)
    
                if cat == "Copyright violations":
                    copyvio_reason = get_copyvio_reason(file_name)
                    copyvio_reason = re.sub("\(\[\[User talk.*?Talkpagelinktext|[{}]","",copyvio_reason)
                    message = message.replace("|2=", "|2=%s" % copyvio_reason)
                
                if cat == "Other speedy deletions":
                    ot_sd_reason = get_other_speedy_reason(file_name)
                    ot_sd_reason = re.sub("\(\[\[User talk.*?Talkpagelinktext|[{}]","",ot_sd_reason)
                    message = message.replace("|2=", "|2=%s" % ot_sd_reason)
                    
                new_text = new_text + message
                summary = "Notification - [[Category:%s|%s]] - [[:%s]]" % (cat, cat, file_name)

            else:
                if "And also:" not in new_text:
                    new_text = new_text + "\nAnd also:"
                if nominator:
                    nominator_details = "Nominator : {{Noping|%s}}" % nominator
                else:
                    nominator_details = ""
                
                reason = ""
                
                if cat == "Copyright violations":
                    copyvio_reason = re.sub("\(\[\[User talk.*?Talkpagelinktext|[{}]","",get_copyvio_reason(file_name))
                    reason = "- Reason : %s" % copyvio_reason

                _file_info = """* [[:%s]] <p style="font-size:0.8em;font-family:'Stencil Std'">( %s %s )</p>""" % (file_name , nominator_details, reason)
                new_text = new_text + _file_info
                
                summary = "Notification - [[Category:%s|%s]] - [[:%s]] and %d other files" % (cat, cat, file_name, file_count)
        
        if file_count < 1:
            continue

        new_text = new_text + "\nI'm a computer program; please don't ask me questions but ask the user who nominated your file(s) for deletion or at our [[Commons:Help_desk|Help Desk]]. //~~~~"
        
        new_text = uploader_talk_page.get() + new_text
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

