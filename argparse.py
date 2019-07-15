# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# argparse.py # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 09 July 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def parse(arg_str, argv):
    arg_dict = {}
    res_list = []
    
    for i in range(0, len(arg_str)):
        if arg_str[i] == ":":
            continue
        arg_dict.update({"-"+arg_str[i]: False})
        if i+1 != len(arg_str) and arg_str[i+1] == ":":
            arg_dict["-"+arg_str[i]] = True

    for i in range(1, len(argv)):
        # if the argument is recognized
        if argv[i] in arg_dict:
            # if the argument requires a subarg
            if arg_dict[argv[i]]:
                # if i is big enough and the next
                # argument is not in arg_dict
                if i+1 != len(argv) and argv[i+1] not in arg_dict:
                    res_list.append((argv[i], argv[i+1]))
                    i += 2
                else:
                    res_list.append((argv[i], None))

            # if it doesn't require a subarg
            else:
                res_list.append((argv[i], True))
        else:
            res_list.append(argv[i], None)

    return res_list
