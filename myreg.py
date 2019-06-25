import re

re_str = r"\w+\.\w{2,6}\/"
my_regex = re.compile(re_str)

fi = open('nfm.json', 'r').read()
s = my_regex.findall(fi)

wf = open("matches2.txt", "w")
for match in s:
    wf.write(match + '\n')
