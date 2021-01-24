function dl() {
  curl https://raw.githubusercontent.com/$1/$2/master$3/pom.xml -o ${2}_pom.xml
}
dl sleberknight mvn-deps-generator
dl apache maven-shade-plugin
dl junit-team junit5-samples /junit5-jupiter-starter-maven
pip install --user xmldiff
