import requests
import re
import yaml
import json
import logging
from bs4 import BeautifulSoup, NavigableString, Tag

logging.basicConfig(level=logging.INFO)

api_re = re.compile(r'api/(.+?)\.md')
source_uri = "https://docs.microsoft.com/en-US/graph/api/{api_name}?view=graph-rest-{version}"
api_toc_yaml_v1 = "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs/master/api-reference/v1.0/toc.yml"
api_toc_yaml_beta = "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs/master/api-reference/beta/toc.yml"
permission_uri = "https://docs.microsoft.com/en-us/graph/permissions-reference"


def get_permission_list():
    logging.debug("get source     : {}".format(permission_uri))
    r = requests.get(permission_uri)

    logging.debug("convert to json: {}".format(permission_uri))

    b = BeautifulSoup(r.content, features="html.parser")
    tables = b.find_all('table')
    permission_list = []

    for table in tables:
        table_header = table.find_previous().text

        if 'delegated permissions' in table_header.lower():
            permission_list = permission_list + permission_name_table_to_json(table, 'delegated')        
        elif 'application permissions' in table_header.lower():
            permission_list = permission_list + permission_name_table_to_json(table, 'application')

    return permission_list

def permission_name_table_to_json(table, type):
    permission_list = []
    trs = table.find('tbody').find_all('tr')
    for tr in trs:
        tds = tr.find_all('td')
        if len(tds) < 4:
            continue

        permission = {
            "id": type + "_" +  tds[0].text,
            "name": tds[0].text,
            "displayString": tds[1].text,
            "description": tds[2].text,
            "needAdminConsent": True if tds[3].text == "Yes" else False,
            "type": type
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
        if "items" in api and api["items"]:
            api_names = api_names + __get_api_names_recurse(api["items"])
                
    return api_names


def get_api_names(api_toc_yaml=api_toc_yaml_v1, version="1.0"):
    data = yaml.load(requests.get(api_toc_yaml).content, yaml.SafeLoader)
    v = version
    if version == "1.0":
        v = "v1.0"
    api_reference_links = [r for r in data['items']
                           if r["name"].lower() == "{} reference".format(v)][0]["items"]
    
    return sorted(list(set(__get_api_names_recurse(api_reference_links))))


def save_source_html(api_toc_yaml=api_toc_yaml_v1,api_version="1.0"):
    api_names = get_api_names(api_toc_yaml, api_version)
    api_version = "1.0"
    for api_name in api_names:
        try:
            u = source_uri.format(api_name=api_name, version=api_version)
            r = requests.get(u)
            with open("api_source/" + api_name + ".html", "wb") as f:
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

            parags = overview.find_all('p')
            
            # skip warning for beta api
            # 
            # <div class="alert is-primary">
            #     <p class="alert-title"><span class="docon docon-status-info-outline" aria-hidden="true"></span> Important</p>
            #     <p>APIs under the <code>/beta</code> version in Microsoft Graph are subject to change. Use of these APIs in production applications is not supported.</p>
            # </div>
            #
            if parags[1].text == "Important":
                description = parags[3]
            else:
                description = parags[1]

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
                ',') if p != ""] if not "Not supported." in td.text else None
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

def get_api_detail(api_toc_yaml=api_toc_yaml_v1, version="1.0"):
    names = get_api_names(api_toc_yaml=api_toc_yaml, version=version)
    results = []
    count = len(names)
    logging.info("api name count : {}".format(count))
    i = 0
    for name in names:
        i = i + 1
        logging.info("step           : {}/{}".format(i, count))

        source = source_uri.format(api_name=name, version=version)
        try:
            logging.info("get source     : {}".format(source))
            html = requests.get(source).content
            logging.info("convert to json: {}".format(source))
            j = html_to_json(html, source)
            results.append(j)
        except Exception as e:
            logging.warning(e)
            raise e
    return results

def merge_beta_api_to_v1(v1, beta):
    v1_api_names = [api["name"] for api in v1]
    additional_api = [b for b in beta if not b["name"] in v1_api_names]
    for a in additional_api:
        a["isBeta"] = True

    return v1 + additional_api

if __name__ == "__main__":
    api_version="1.0"
    p = get_permission_list()
    with open('vue-spa/src/permissions.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(p, indent="  "))

    v1 = get_api_detail()
    with open('vue-spa/src/api_v1.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(v1, indent="  "))

    beta = get_api_detail(api_toc_yaml=api_toc_yaml_beta, version="beta")
    with open('vue-spa/src/api_beta.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(beta, indent="  "))


    # with open('vue-spa/src/api_v1.json', 'r', encoding='utf-8') as f:
    #     v1 = json.load(f)

    # with open('vue-spa/src/api_beta.json', 'r', encoding='utf-8') as f:
    #     beta = json.load(f)

    merged = merge_beta_api_to_v1(v1, beta)

    with open('vue-spa/src/api.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(merged, indent="  "))
