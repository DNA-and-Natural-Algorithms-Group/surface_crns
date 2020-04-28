import os,sys,random
from surface_crns.models.grids import *
from surface_crns.simulators.queue_simulator import *
from surface_crns.readers.manifest_readers import read_manifest
from surface_crns.options.option_processor import SurfaceCRNOptionParser

'''
Run a molecular rugby competition between any number of teams. 

First, put all of your teams' strategies in the "Teams" folder. Each strategy 
needs a text file with all of the rules for team movement, written for team X. 
There are a number of examples you can look at. 

Invoke with:

python rugbycompete.py <# points>

Where <# points> (optional) is the number of games played between each pair. 

This will play each team against each other 2*<# points> times, switching X/Y 
roles halfway through. A team wins if it beats the other team by at least 
sqrt(<# points>) points. Results are printed in a file with a random label in 
the "results" folder. 

If you want results to be repeatable, manually set the SEED variable below to 
an integer other than 0. 
'''

SEED = 0
results_loc = "results"
teamfile_loc = "Teams"
manifest_file = "templated_rugby_manifest.txt"

def main():
  if len(sys.argv) < 2:
    print("Using default 100 points per matchup.")
    n_points = 100
  else:
    n_points = int(sys.argv[1])

  # Always randomize the results filename (avoiding collisions) to avoid 
  # overwriting an old one. 
  # THEN set the random seed for simulations for replicability.
  all_results = [f for f in os.listdir(results_loc) 
                  if os.path.isfile(os.path.join(results_loc, f))]  
  used_uids = [filename.split(".")[0].split("_")[-1] 
               for filename in all_results]

  random.seed(0)
  while True:
    uid = random.randint(1,1000000)
    if uid not in used_uids:
      break
  result_file = os.path.join('results', f'competition_manifest_{uid}.txt')

  random.seed(SEED)
  
  teams = [f for f in os.listdir(teamfile_loc) if f.endswith(".txt")]
  teamnames = [filename.split(".")[0] for filename in teams]

  K=len(teams)

  score=[[(0,0) for i in range(K)] for j in range(K)]
  for i in range(K):
    for j in range(K):
      if not i==j:
        #print(f"\n({i*K + j+1}/{K*K}) ", end = "")
        #print(f"Playing {teamnames[i]} vs. {teamnames[j]}\t\t", end = "")
        create_strategy_insert(teams[i], teams[j])
        score[i][j] = compete_teams(teams[i], teams[j], n_points, manifest_file)
        print('Finished competing team {} against team {}.'.format(i,j))

  print()
  line = "{:<30}  ".format("")
  for j in range(K):
      teamabrv= "".join([w[0] for w in teams[j].split("_")])
      line=line+" {:^7} ".format(teamabrv)
  print(line)
  for i in range(K):
    line = "{:<30} :".format(teams[i])
    for j in range(K):
        line=line+" {:>3}/{:<3} ".format(score[i][j][0],score[i][j][1])
    print(line)
  print()

  wins=[0 for i in range(K)]
  for i in range(K):
      for j in range(K):
          if not i==j:
              wins[i]=wins[i]+int(score[i][j][0]>score[i][j][1])
              wins[i]=wins[i]+int(score[j][i][1]>score[j][i][0])
  totals=[0 for i in range(K)]
  for i in range(K):
      for j in range(K):
          if not i==j:
              totals[i]=totals[i]+score[i][j][0]
              totals[i]=totals[i]+score[j][i][1]
              
  ranked=sorted(range(K), key=lambda k: -wins[k])
  for k in range(K):            
      print('Team {} won {} points against other teams, while beating {} teams.'.format(teams[ranked[k]],totals[ranked[k]],wins[ranked[k]]))
  print()

  # os.remove(manifile)


def create_strategy_insert(teamXfile,teamYfile):
  with open(os.path.join("temp", "strategy_insert.txt"), 'w') as strategy_file:
    with open(os.path.join(teamfile_loc, teamXfile), 'r') as x_infile:
      for line in x_infile:
        strategy_file.write(line)

    with open(os.path.join(teamfile_loc, teamXfile), 'r') as y_infile:
      for line in y_infile:
        strategy_file.write(line.replace("X", "Y"))

def run_game(manifest_file):
    '''Input: manifest file name
       Output: string representing winner'''
    manifest_options = read_manifest(manifest_file)
    opts = SurfaceCRNOptionParser(manifest_options)

    lattice = SquareGrid(27, 19, wrap=False)
    lattice.set_global_state(opts.init_state)

    simulator = QueueSimulator(surface = lattice,
                                transition_rules = opts.transition_rules,
                                seed = opts.rng_seed,
                                simulation_duration = opts.max_duration)

    while not simulator.done():
        # faster to let simulation complete than to check for winner at
        # each step
        simulator.process_next_reaction()

    end_state = simulator.surface.get_global_state()
    if 'WX' in [j for i in end_state for j in i]:
        return 'X'
    elif 'WY' in [j for i in end_state for j in i]:
        return 'Y'
    return 'N'

def compete_teams(teamXfile, teamYfile, n_points, manifest_file):
  print(f'Competing {teamXfile} against {teamYfile} for {n_points} games.')
  res = [run_game(manifest_file) for i in range(n_points)]
  Xpoints = sum([(i=='X') for i in res])
  Ypoints = sum([(i=='Y') for i in res])
  print('X (%s) wins %d times' % (teamXfile,Xpoints))
  print('Y (%s) wins %d times' % (teamYfile,Ypoints))
  print('%d ties' % (sum([(i=='N') for i in res])))
  return (Xpoints,Ypoints)


if __name__ == "__main__":
  main()
