import random
import re
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer


def check_is_confirm_button(view: dict, debug=False):
    confirm_button = ["save", "add", "create", "done", "ok", "confirm", "sign", "next", "unlock", "setup", "search",
                      "login"]
    confirm_button = set(confirm_button)
    confirm_words = ["log in"]
    refer_name = view["refer_name"].lower()
    view_class = view["class"]
    refer_name_words = set(refer_name.split())
    is_confirm_button = len(refer_name_words.intersection(confirm_button)) > 0 or refer_name in confirm_words
    is_button = view_class[-8:].lower() == "textview" or (view_class[-6:].lower() in ["button", "layout"])
    view_bounds = view["bounds"]
    view_centerx = (view_bounds[0][0] + view_bounds[1][0]) / 2
    view_centery = (view_bounds[0][1] + view_bounds[1][1]) / 2
    if view["neighbor_text"].lower() == "plant details" and view["refer_name"] == "navigate up":
        return True
    if view_centerx < 250 and view_centery < 150:
        return False
    if debug:
        print("refer_name:", refer_name)
        print("refer_name_words:", refer_name_words)
        print("intersection:", len(refer_name_words.intersection(confirm_button)))
    return is_confirm_button and is_button

def get_view_refer_name(view_info):
    # Priority 1: for EditText, return its resource id for name, or neighbor text
    if view_info["class"][-8:].lower() == "edittext":
        return get_edittext_name(view_info)

    # Priority 2: for checkbox, radiobutton, switch, return its neighbor text for name
    if view_info["class"][-8:].lower() == "checkbox" or view_info["class"][-11:].lower() == "radiobutton" \
            or view_info["class"][-6:].lower() == "switch":
        return get_checktext_name(view_info)

    # Priority 3: case layout, text from child
    if view_info["class"][-6:].lower() == "layout" or view_info["class"][-7:].lower() == "spinner":
        return get_layout_name(view_info)

    return get_general_name(view_info)


def get_edittext_name(view_info):
    # EditText 1: for EditText, return its resource id for name, or neighbor text
    if view_info["resource_id"] != "none" and len(view_info["resource_id"].split()) > 1:
        clean_id = clean_resource_id(view_info["resource_id"])
        keywords = ["email", "name", "pass"]
        has_keyword = False
        for keyword in keywords:
            if keyword in clean_id:
                has_keyword = True
                break
        has_sibling_text = len(view_info["sibling_text"]) > 0 and view_info["sibling_text"][0] != "none"
        use_flag1 = (len(clean_id.split()) >= 2 and len(clean_id.split()) <= 3)
        use_flag2 = (not has_sibling_text) and (len(clean_id.split()) == 1 or len(clean_id.split()) >= 4)
        if use_flag1 or use_flag2 or has_keyword:
            return clean_id

    # EditText 2: return not none sibling text
    if len(view_info["sibling_text"]) > 0:
        for sibling_text in view_info["sibling_text"]:
            if sibling_text != "none":
                return sibling_text.lower()

    # EditText 3: return not none parent text
    if view_info["parent_text"] != "none":
        return view_info["parent_text"].lower()

    # EditText 3: no idea what to return, return neighbor text
    return view_info["neighbor_text"].lower()


def get_checktext_name(view_info):
    # checktext 1: for checkbox, radiobutton, switch, return its neighbor text for name
    if len(view_info["sibling_text"]) > 0:
        for sibling_text in view_info["sibling_text"]:
            if sibling_text != "none":
                return sibling_text.lower()

    # checktext 2: no idea what to return, return neighbor text
    return view_info["neighbor_text"].lower()


def get_layout_name(view_info):
    # layout 1: case layout, text from child
    if len(view_info["child_text"]) > 0:
        return view_info["child_text"][0][0].lower()

    # layout 2: case layout, text from child
    if view_info["resource_id"] != "none":
        clean_id = clean_resource_id(view_info["resource_id"])
        if len(clean_id.split(" ")) >= 1 and len(clean_id.split(" ")) <= 4:
            # return view_info["resource_id"].lower()
            return clean_id

    # layout 3: no idea what to return, return neighbor text
    return view_info["neighbor_text"].lower()


def get_general_name(view_info):
    # Priority 1: text from self
    if view_info["text"] != "none":
        return view_info["text"].lower()
    if view_info["content_desc"] != "none":
        return view_info["content_desc"].lower()
    if view_info["hint"] != "none":
        return view_info["hint"].lower()

    # Priority 2: view's resource id longer than 2 words, it may be a meaningful identifier
    if view_info["resource_id"] != "none":
        clean_id = clean_resource_id(view_info["resource_id"])
        if len(clean_id.split(" ")) >= 1 and len(clean_id.split(" ")) <= 4:
            # return view_info["resource_id"].lower()
            return clean_id

    # Priority 3: return not none sibling text
    if len(view_info["sibling_text"]) == 1 and view_info["sibling_text"][0] != "none":
        return view_info["sibling_text"][0].lower()

    # Priority 4: return only one child_text
    if len(view_info["child_text"]) == 1 and view_info["child_text"][0][0] != "none":
        return view_info["child_text"][0][0].lower()

    # Priority 5: no idea what to return, return neighbor text
    # to avoid noise, drop such case in train set
    return ""
    # if view_info["class"][-6:].lower == "button" or view_info["class"][-8:].lower() == "textview":
    #     rand_num = random.random()
    #     if rand_num < 0.5:
    #         return ""
    #     else:
    #         return view_info["neighbor_text"].lower()
    # else:
    #     return view_info["neighbor_text"].lower()

def clean_resource_id(resource_id: str):
    resource_id = resource_id.lower()
    resource_id = re.sub("[^a-z]", " ", resource_id).strip()
    useless_words = ["edittext", "button", "none", "view", "textview", "fab", "action", "icon"]
    words = resource_id.strip().split(" ")
    use_word = []
    for word in words:
        word_char = set(word)
        # drop word that maybe abbreviation from edittext/button, like: edit, edt, ed, text...
        use_flag = True
        for useless_word in useless_words:
            inter_with_useless_word = word_char.intersection(set(useless_word))
            if len(word_char) <= len(inter_with_useless_word):
                use_flag = False
                break
        if use_flag:
            use_word.append(word)
    if len(use_word) == 0:
        return "none"
    else:
        return " ".join(use_word)
