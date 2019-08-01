#!/bin/sh

cd $(dirname $0)
if [ ! -d $HOME/.local/share/exaile/plugins/pradio ]; then
    mkdir -p $HOME/.local/share/exaile/plugins
    cp -r pradio $HOME/.local/share/exaile/plugins
fi
