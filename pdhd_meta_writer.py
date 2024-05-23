import json
from argparse import ArgumentParser as ap


if __name__ == '__main__':
  parser = ap()
  parser.add_argument('--json', type=str, default=None)
  parser.add_argument('--overrides', type=str, nargs='+') ##TODO -- Write help
  parser.add_argument('--parent', type=str, default=None)
  parser.add_argument('--inherit_run', action='store_true')
  parser.add_argument('-o', type=str, required=True)
  parser.add_argument('--jobid')
  #parser.add_argument('--run', type=int, default=1)
  parser.add_argument('--filenum', type=int, default=1)
  parser.add_argument('--event', type=int, default=1)
  parser.add_argument('--nevents', type=int, required=True)
  parser.add_argument('--past_fcls', type=str, nargs='+')
  parser.add_argument('--past_apps', type=str, nargs='+')
  parser.add_argument('--exclude', type=str, nargs='+')
  #parser.add_argument('--momentum', type=float, default=1.)
  args = parser.parse_args()

  if args.json is not None:
    if args.o == args.json:
      raise ValueError("Cannot use same name as input json")
    with open(args.json, 'r') as f:
      in_dict = json.load(f)
  else:
    in_dict = {
      'metadata': {}
    }

  #print(in_dict)

  if args.exclude is not None:
    for exc in args.exclude:
      if exc in in_dict['metadata'].keys():
        del in_dict['metadata'][exc]

  if args.overrides is not None:
    for override in args.overrides:
      split = override.split('=')
      #print(split[0], split[1])
      val = split[1]
      if 'time' in split[0].lower():
        val = float(val)
      in_dict['metadata'][split[0]] = val #split[1]

  #print(in_dict)

  if args.parent is not None:
    name = args.parent.split(':')[1]
    namespace = args.parent.split(':')[0]
    in_dict['parents'] = [
      {"name": name,
       "namespace": namespace 
      }
    ]

  in_dict['metadata']['core.event_count'] = args.nevents
  if args.inherit_run and args.parent is not None:
    from metacat.webapi import MetaCatClient
    mc = MetaCatClient()
    parent_dict = mc.get_file(did=args.parent, with_provenance=False)
    parent_metadata = parent_dict['metadata']
    in_dict['metadata']['core.runs'] = parent_metadata['core.runs']
    in_dict['metadata']['core.runs_subruns'] = parent_metadata['core.runs_subruns']
    in_dict['metadata']['core.first_event_number'] = (
        parent_metadata['core.first_event_number'])
    in_dict['metadata']['core.last_event_number'] = (
        parent_metadata['core.first_event_number'] + args.nevents - 1)
  else:
    if type(args.jobid) is str:
      run=int(args.jobid.split('.')[0])
    else:
      run = args.jobid 
    in_dict['metadata']['core.runs'] = [run]
    in_dict['metadata']['core.runs_subruns'] = [run*10**5 + args.filenum]
    in_dict['metadata']['core.first_event_number'] = args.event
    in_dict['metadata']['core.last_event_number'] = (
        args.event + args.nevents - 1)

  if args.past_fcls is not None:
    if args.past_apps is None or len(args.past_fcls) != len(args.past_apps):
      raise ValueError('Need to provide same number of past apps and fcls')

    in_dict['metadata']['origin.applications.names'] = args.past_apps
    in_dict['metadata']['origin.applications.config_files'] = {
      args.past_apps[i]:args.past_fcls[i] for i in range(len(args.past_apps))
    }

    in_dict['metadata']['origin.applications.versions'] = {
      args.past_apps[i]:in_dict['metadata']['core.application.version']
      for i in range(len(args.past_apps))
    }


  # Serializing json
  json_object = json.dumps(in_dict, indent=2)
   
  # Writing to sample.json
  with open(args.o, "w") as outfile:
    outfile.write(json_object)

