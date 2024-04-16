# #!/bin/sh

# Using https://validator.github.io/validator/


DIRECTORY_PATH="out"
REGEXP=".*(Trailing.slash|Consider.adding.a..lang.|Consider.using.the..h1..element.as.a.top.level.heading.only).*"

# show info/warnings and errors
PARAMS='--format gnu --asciiquotes '$DIRECTORY_PATH

# only show errors
PARAMS='--errors-only '$PARAMS

HTML_PARAMS='--filterpattern '$REGEXP' '$PARAMS

echo $HTML_PARAMS

echo "HTML:"
vnu --skip-non-html $HTML_PARAMS

echo -e "\n\n\n CSS:"
vnu --skip-non-css  $PARAMS

echo -e "\n\n\n SVG:"
vnu --skip-non-svg  $PARAMS
