#!/usr/bin/env python

import re


def iteritems(d):
    if hasattr(dict, "iteritems"):
        return d.iteritems()
    else:
        return iter(d.items())


def additional_properties(data):
    "This recreates the behaviour of kubectl at https://github.com/kubernetes/kubernetes/blob/225b9119d6a8f03fcbe3cc3d590c261965d928d0/pkg/kubectl/validation/schema.go#L312"
    new = {}
    try:
        for k, v in iteritems(data):
            new_v = v
            if isinstance(v, dict):
                if "properties" in v:
                    if "additionalProperties" not in v:
                        v["additionalProperties"] = False
                new_v = additional_properties(v)
            else:
                new_v = v
            new[k] = new_v
        return new
    except AttributeError:
        return data


def replace_int_or_string(data):
    new = {}
    try:
        for k, v in iteritems(data):
            new_v = v
            if isinstance(v, dict):
                if "format" in v and v["format"] == "int-or-string":
                    new_v = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
                else:
                    new_v = replace_int_or_string(v)
            elif isinstance(v, list):
                new_v = list()
                for x in v:
                    new_v.append(replace_int_or_string(x))
            else:
                new_v = v
            new[k] = new_v
        return new
    except AttributeError:
        return data


def allow_null_optional_fields(data, parent=None, grand_parent=None, key=None):
    new = {}
    try:
        for k, v in iteritems(data):
            new_v = v
            if isinstance(v, dict):
                new_v = allow_null_optional_fields(v, data, parent, k)
            elif isinstance(v, list):
                new_v = list()
                for x in v:
                    new_v.append(allow_null_optional_fields(x, v, parent, k))
            elif isinstance(v, str):
                is_non_null_type = k == "type" and v != "null"
                has_required_fields = grand_parent and "required" in grand_parent
                is_required_field = (
                    has_required_fields and key in grand_parent["required"]
                )
                if is_non_null_type and not is_required_field:
                    new_v = [v, "null"]
            new[k] = new_v
        return new
    except AttributeError:
        return data


def change_dict_values(d, prefix, version):
    new = {}
    try:
        is_nullable = False
        for k, v in iteritems(d):
            if k == "nullable":
                is_nullable = True
            new_v = v
            if isinstance(v, dict):
                new_v = change_dict_values(v, prefix, version)
            elif isinstance(v, list):
                new_v = list()
                for x in v:
                    new_v.append(change_dict_values(x, prefix, version))
            elif isinstance(v, str):
                if k == "$ref":
                    if version < "3":
                        new_v = "%s%s" % (prefix, v)
                    else:
                        new_v = v.replace("#/components/schemas/", "") + ".json"
            else:
                new_v = v
            new[k] = new_v
        if is_nullable and "type" in new:
            if not isinstance(new["type"], list):
                new["type"] = [new["type"]]
            new["type"].append("null")
        return new
    except AttributeError:
        return d


def append_no_duplicates(obj, key, value):
    """
    Given a dictionary, lookup the given key, if it doesn't exist create a new array.
    Then check if the given value already exists in the array, if it doesn't add it.
    """
    if key not in obj:
        obj[key] = []
    if value not in obj[key]:
        obj[key].append(value)


def get_components_from_body_definition(body_definition, prefix=""):
    MIMETYPE_TO_TYPENAME_MAP = {
        "application/json": "json",
        "application/vnd.api+json": "jsonapi",
    }
    result = {}
    for mimetype, definition in body_definition.get("content", {}).items():
        type_name = MIMETYPE_TO_TYPENAME_MAP.get(
            mimetype,
            mimetype.replace("/", "_"),
        )
        if "schema" in definition:
            result["{:s}{:s}".format(prefix, type_name)] = definition["schema"]
    return result


def get_body_file_prefix(path, http_method):
    name_prefix_fmt = "paths_{:s}_{:s}_{{:s}}_".format(
        # Paths "/" and "/root" will conflict,
        # no idea how to solve this elegantly.
        path.lstrip("/").replace("/", "_") or "root",
        http_method,
    )
    return re.sub(
        r"\{([^:\}]+)\}",
        r"_\1_",
        name_prefix_fmt,
    )


def get_request_and_response_body_components_from_paths(paths):
    components = {}
    for path, path_definition in paths.items():
        for http_method, http_method_definition in path_definition.items():
            name_prefix_fmt = get_body_file_prefix(path, http_method)
            if "requestBody" in http_method_definition:
                components.update(
                    get_components_from_body_definition(
                        http_method_definition["requestBody"],
                        prefix=name_prefix_fmt.format("request"),
                    )
                )
            responses = http_method_definition["responses"]
            for response_code, response in responses.items():
                response_name_part = "response_{}".format(response_code)
                components.update(
                    get_components_from_body_definition(
                        response,
                        prefix=name_prefix_fmt.format(response_name_part),
                    )
                )
    return components


def get_request_parameters_from_paths(paths, parameters):
    components = {}
    for path, path_definition in paths.items():
        for http_method, http_method_definition in path_definition.items():
            component = {}
            if "parameters" in http_method_definition:
                component["properties"] = {}
                required = []
                for param_value in http_method_definition["parameters"]:
                    if "$ref" in param_value:
                        tmp = param_value["$ref"]
                        tmp = tmp.replace("#/components/parameters/", "")
                        external_param = parameters[tmp]
                        name = external_param["name"]
                        component["properties"][name] = {"in": external_param["in"]}

                        for key in external_param["schema"]:
                            component["properties"][name][key] = external_param["schema"][key]

                        if external_param["required"]:
                            required.append(name)
                    else:
                        name = param_value["name"]
                        component["properties"][name] = {"in": param_value["in"]}

                        for key in param_value["schema"]:
                            component["properties"][name][key] = param_value["schema"][key]

                        if param_value["required"]:
                            required.append(name)
                if required:
                    component["required"] = required
            if "requestBody" in http_method_definition:
                content = http_method_definition["requestBody"]["content"]
                schema = content["application/json"]["schema"]
                if "$ref" in schema:
                    tmp = schema["$ref"]
                    tmp = tmp.replace("#/components/schemas/", "") + ".json"
                    component["requestBody"] = tmp.lower()
                else:
                    prefix_fmt = get_body_file_prefix(path, http_method)
                    prefix = prefix_fmt.format("request")
                    component["requestBody"] = prefix + "json.json"
            operation_id = http_method_definition["operationId"]
            components[operation_id] = component

    return components


def parse_headers(header):
    """
    Argument is a tuple of header strings.
    e.g. ('Content-Type: application/json', 'Accept: application/text')
    Invalid headers are ignored.
    The function returns a dictionary of the headers.
    """
    res = {}
    for h in header:
        h = h.split(":", 1)
        if len(h) == 2:
            res[h[0].strip()] = h[1].strip()
    return res
