if [[ -f .venv/bin/activate ]]; then
   export PYTHONPATH=$(readlink -f .)

   source .venv/bin/activate
fi
