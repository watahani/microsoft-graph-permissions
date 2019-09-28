import requests
import re
import yaml
import json
from bs4 import BeautifulSoup, NavigableString, Tag

api_re = re.compile(r'api/(.+?)\.md')
source_uri = "https://docs.microsoft.com/en-US/graph/api/{}?view=graph-rest-1.0"
api_reference_yaml = "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs/master/api-reference/v1.0/toc.yml"
permission_uri = "https://docs.microsoft.com/en-us/graph/permissions-reference"

def get_permission_list():
    r = requests.get(permission_uri)
    b = BeautifulSoup(r.content, features="html.parser")
    trs = b.find_all('tr')
    permission_list = []
    for tr in trs:
        if tr.parent.name == "tbody":
            tds = tr.find_all('td')
            if len(tds) < 4:
                continue

            permission = {
                "name": tds[0].text,
                "displayString": tds[1].text,
                "description": tds[2].text,
                "needAdminConsent": True if tds[3].text == "Yes" else False
            }
            if len(tds) > 4:
                permission['isMsaSupported'] = True if tds[4].text == "Yes" else False
            permission_list.append(permission)
    return permission_list


def __get_api_names_recurse(source):
    api_names = []
    for api in source:
        if "href" in api:
            if api_re.match(api["href"]):
                api_name = api_re.match(api["href"]).group(1)
                if api_name:
                    api_names.append(api_name)
        if "items" in api:
            api_names = api_names + __get_api_names_recurse(api["items"])
    return api_names


def get_api_names(api_reference_yaml_path):
    headers = {"Accept-Language": "en-US,en;q=0.5"}
    data = yaml.load(requests.get(api_reference_yaml,
                                  headers=headers).content, yaml.SafeLoader)

    api_reference_links = [r for r in data[0]['items']
                           if r["name"] == "v1.0 reference"][0]["items"]

    return set(__get_api_names_recurse(api_reference_links))


def save_source_html():
    api_names = get_api_names(api_reference_yaml)

    for b in api_names:
        try:
            u = source_uri.format(b)
            r = requests.get(source_uri.format(b))
            with open("api_source/" + b + ".html", "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(e)
            pass


def html_to_json(html, source_uri=None):
    b = BeautifulSoup(html, features="html.parser")
    api = {
        "sourceUri": source_uri,
        "name": b.h1.text
    }

    tags = [tag for tag in b.main.children if tag.__class__ == Tag]

    for tag in tags:
        if not 'id' in tag.attrs:
            continue

        attrs_id = tag.attrs['id']
        c = ""
        for elm in tag.next_siblings:
            if elm.__class__ == Tag:
                if 'id' in elm.attrs and (elm.name == 'h2' or elm.name == 'h3'):
                    break
                c = c + str(elm)
                # print(elm)
        # description
        if tag.name == 'h1':
            overview = BeautifulSoup(c, features="html.parser")
            update_time = overview.time
            api['datetime'] = update_time.attrs.get('datetime', None) if (
                update_time and update_time.attrs) else None

            description = overview.p
            api["description"] = description.text

        elif attrs_id == 'permissions':
            api['permissions'] = get_permissions(c)

        elif attrs_id == "prerequisites":
            api['prerequisites'] = get_permissions(c)

        elif attrs_id == 'http-request':
            pass

        elif attrs_id == 'request-body':
            pass

        elif attrs_id == 'request':
            pass

        elif attrs_id == "request-headers":
            pass

        elif attrs_id == "example":
            pass

        else:
            pass
            # if not "attrs_error" in api:
            #     api["attrs_error"] = [attrs_id]
            # else:
            #     api["attrs_error"].append(attrs_id)

    return api


def get_permissions(c):
    p = {}
    error = []
    for tr in BeautifulSoup(c, features="html.parser").find_all('tr'):
        if tr and tr.td:
            permission_type = tr.td.text
            permission_type_key = None

            if "(work or school account)" in permission_type:
                permission_type_key = "delegated"
            elif "(personal Microsoft account)" in permission_type:
                permission_type_key = "msa"
            elif "Application" in permission_type:
                permission_type_key = "application"
            else:
                error.append(permission_type)
            td = tr.find_all('td')
            td = td[len(td) - 1]
            permissions = [p.strip() for p in td.text.split(
                ',')] if not "Not supported." in td.text else None
            p[permission_type_key] = permissions

    if len(error) > 0:
        return "Need permission for resources. For more details, check document"
        # return {
        #     "error": error
        # }
    return p


def debug(name):
    with open("api_source/{}.html".format(name), "r", encoding='utf-8') as f:
        html = f.read()
        j = html_to_json(html)
        print(json.dumps(j, indent="  "))
        exit()


if __name__ == "__main__":
    # import time
    # start = time.time()
    # file()
    # process_time = time.time() - start
    # print(process_time)
    p = get_permission_list()
    with open('vue-spa/src/permissions.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(p, indent="  "))

    names = get_api_names(api_reference_yaml)
    result = []

    for name in names:
        source = source_uri.format(name)
        with open("api_source/{}.html".format(name), "r", encoding='utf-8') as f:
            html = f.read()
            j = html_to_json(html, source)
            result.append(j)
    with open('vue-spa/src/api.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, indent="  "))
    

