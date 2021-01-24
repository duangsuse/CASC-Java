for name in junit5-samples mvn-deps-generator; do
  echo "testing ${name}"
  ../mvng.py @$name.resp -o .
  xmldiff pom.xml ${name}_pom.xml -p -F .01
done
