#!/bin/bash
## begin license ##
#
# "Meresco Lucene" is a set of components and tools to integrate Lucene (based on PyLucene) into Meresco
#
# Copyright (C) 2013-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
#
# This file is part of "Meresco Lucene"
#
# "Meresco Lucene" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Lucene" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Lucene"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

set -o errexit

mydir=$(cd $(dirname $0); pwd)
buildDir=$mydir/build
jarsDir=$(dirname $mydir)/jars
libDir=$1
if [ -z "$libDir" ]; then
    libDir=$(dirname $mydir)/lib
fi

rm -rf $buildDir $libDir
mkdir --parents $buildDir $libDir

pythonVersion=$(python --version 2>&1 | awk '{print $2}' | cut -d. -f-2)

javac=/usr/lib/jvm/java-1.7.0-openjdk.x86_64/bin/javac
if [ ! -f "$javac" ]; then
    javac=/usr/lib/jvm/java-1.7.0/bin/javac
fi

luceneJarDir=/usr/lib64/python${pythonVersion}/site-packages/lucene
if [ -f /etc/debian_version ]; then
    javac=/usr/lib/jvm/java-7-openjdk-amd64/bin/javac
    luceneJarDir=/usr/lib/python${pythonVersion}/dist-packages/lucene
fi

PYLUCENEVERSION=4.10.1

classpath=${luceneJarDir}/lucene-core-$PYLUCENEVERSION.jar:${luceneJarDir}/lucene-analyzers-common-$PYLUCENEVERSION.jar

${javac} -cp ${classpath} -d ${buildDir} `find . -type f \( -path "*analysis*" \)`
(cd $buildDir; jar -c org > $buildDir/meresco-lucene.jar)

python -m jcc.__main__ \
    --root $mydir/root \
    --use_full_names \
    --import lucene \
    --shared \
    --arch x86_64 \
    --jar $buildDir/meresco-lucene.jar \
    --python meresco_lucene \
    --build \
    --install

rootLibDir=$mydir/root/usr/lib64/python${pythonVersion}/site-packages/meresco_lucene
if [ -f /etc/debian_version ]; then
    rootLibDir=$mydir/root/usr/local/lib/python${pythonVersion}/dist-packages/meresco_lucene
fi

mv ${rootLibDir} $libDir/

rm -rf $buildDir $mydir/root $mydir/meresco_lucene.egg-info

