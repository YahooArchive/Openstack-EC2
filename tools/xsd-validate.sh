#!/bin/bash

set +x

JRE=`which java`
PWD=`pwd`
LIBS=""
for d in `ls libs`;
do
    LIBS="libs/$d:$LIBS";
done

$JRE -cp $LIBS  XsdValidator $*


