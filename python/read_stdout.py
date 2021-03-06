"""
Written by: Anthony Badea (June 2020)

Takes in an stdout file from the simulation scripts and parses the arguments into a dictionary. 
The main method launches a job with those settings.

"""


import os, sys, argparse, time

# Input: stdout from simulation code src/sim
# Output: dictionary containing parameters to run over
def parse_stdout(stdout = ''):
	file = open(stdout,'r')
	lines = file.readlines()

	inputs = {}
	for line in lines: 
		vals = line.split('>> ')[-1].split(': ')
		# there should be two entries: key, value
		if len(vals) == 1: 
			if 'Background rate' in vals[0]:
				vals = [['Background rate', vals[0].split('Background rate of ')[-1].split(' Hz')[0]]]
			elif 'Generate muons with angle (x)' in vals[0]:
				vals = [['Generate muons with angle (x)',vals[0].split('Generate muons with angle (x) from ')[-1].split(' to ')[-1].split('\n')[0]]]
			elif 'Generate muons with angle (y)' in vals[0]:
				vals = [['Generate muons with angle (y)',vals[0].split('Generate muons with angle (y) from ')[-1].split(' to ')[-1].split('\n')[0]]]
			elif 'Generating' in vals[0]:
				vals = [['nEvents',vals[0].split('Generating ')[-1].split(' events')[0]]]
			else:
				continue
		elif len(vals) == 2:
			if 'Assuming chamber size' == vals[0]:
				vals[1] = [vals[1].split('(')[-1].split(',')[0],vals[1].split(',')[-1].split(')')[0]]
			else:
				vals[1] = vals[1].split('\n')[0]
			vals = [vals]
		elif len(vals) == 3 and 'x-road size' in vals[0]:
			x_road_size = [vals[0].split(' (in')[0], vals[1].split(',')[0]]
			uv_road_size = ['uv-road size', vals[2].split('\n')[0]]
			vals = [x_road_size,uv_road_size]
		else:
			#print('Line longer than 3 long')
			continue

		# Add vals to dictionary
		for val in vals:
			if val[0] not in inputs.keys():
				inputs[val[0]] = val[1]
			else:
				print("Key already in dictionary. Problem!!")
				continue

	return inputs


# Input: dictionary of simulation parameters from parse_stdout
# Output: dictionary prepared for use by batch_local_diff_params
def clean_dict(inputs):
	param_dict = {'nEvents':0,
				  'bkgrate':0,
				  'm_xroad':0,
				  'm_NSTRIPS':0,
				  'm_bcwind':0,
				  'm_sig_art':0,
				  'killran':0,
				  'killxran':0,
				  'killuvran':0,
				  'm_sig_art_x':0,
				  'efficiencies':[],
				  'angx':0,
				  'angy':0,
				  'm_xthr':0,
				  'm_uvthr':0,
				  'pltflag':0,
				  'uvrflag':0,
				  'trapflag':0,
				  'ideal_tp':0,
				  'ideal_vmm':0,
				  'ideal_addc':0,
				  'write_tree':['-tree'], # default this on
				  'smear_art':0,
				  'funcsmear_art':0,
				  'chamber': 0,
				  'legacy':0,
				  'seed':0
	}

	for key, val in inputs.items():
		if 'nEvents' == key:
			param_dict['nEvents'] = ['-n', int(val)]
		elif 'XXX' == key:
			param_dict['m_xroad'] = ['-x',0]
		elif 'Using BCID window' == key:
			param_dict['m_bcwind'] = ['-w',int(val)]
		elif 'Using thresholds (x, uv)' == key:
			param_dict['m_xthr'] = ['-thrx',int(val[1])] # found by looking at key by hand
			param_dict['m_uvthr'] = ['-thruv',int(val[4])] # found by looking at key by hand
		elif 'Using trapezoidal geometry' == key:
			param_dict['trapflag'] = [] if val == 'false' else ['--trap']
		elif 'Assuming chamber size' == key:
			param_dict['chamber'] = ['-ch','large'] if val[1] == '2200.0' else ['-ch','small']
		elif 'art res (in ns)' == key:
			param_dict['m_sig_art'] = ['-sig',int(val)]
		elif 'Background rate' == key:
			param_dict['bkgrate'] = ['-b',int(val)]	
		elif 'plot flag' == key:
			param_dict['pltflag'] = [] if val == 'false' else ['-p']
		elif 'Using UV roads' == key:
			param_dict['uvrflag'] = [] if val == 'false' else ['-uvr']
		elif 'MM efficiency' in key:
			param_dict['efficiencies'].append((int(key.split('chamber ')[-1]),float(val)))
		elif 'Generate muons with angle (x)' == key:
			param_dict['angx'] = ['-angx',float(val)]
		elif 'Generate muons with angle (y)' == key:
			param_dict['angy'] = ['-angy',float(val)]
		elif 'XXX' == key:
			param_dict['XXX'] = ['-angcos',0]
		elif 'Killing one plane randomly' == key:
			param_dict['killran'] = [] if val == 'false' else ['-killran']
		elif 'Killing one X plane randomly' == key:
			param_dict['killxran'] = [] if val == 'false' else ['-killxran']
		elif 'Killing one UV plane randomly' == key:
			param_dict['killuvran'] = [] if val == 'false' else ['-killuvran']
		elif '-999.' == key:
			param_dict['ideal_vmm'] = ['-ideal-vmm',0]
		elif '-999.' == key:
			param_dict['ideal_addc'] = ['-ideal-addc',0]  
		elif '-999.' == key:
			param_dict['ideal_tp'] = ['-ideal-tp',0]
		elif 'Seed for TRandom3' == key:
			param_dict['seed'] = ['-seed', int(val)]
		elif '-999.' == key:
			param_dict['write_tree'] = ['-tree',0]
		elif '-999.' == key:
			param_dict['m_NSTRIPS'] = ['-strips',0]
		elif 'smear art position (gaussian)' == key:
			param_dict['smear_art'] = [] if val == 'false' else ['-smear']
		elif 'XXX' == key:
			param_dict['m_sig_art_x'] = ['-smearstrips',int(val)]
		elif 'smear art position (functional)' == key:
			param_dict['funcsmear_art'] = [] if val == 'false' else ['-funcsmear']
		elif 'XXX' == key:
			param_dict['legacy'] = ['-legacy']		
		
	# Clean up efficiency list
	if len(param_dict['efficiencies']) == 8:
		param_dict['legacy'] = ['-legacy']	

	param_dict['efficiencies'] = sorted(param_dict['efficiencies'])
	param_dict['efficiencies'] = ['-e',[val[1] for val in param_dict['efficiencies']]]
	
	#### DIRTY TEST ####
	param_dict['nEvents'] = ['-n', 1000]

	return param_dict


# Input: list of efficiencies
# Output: string of efficiencies separated by commas
def formatMMEffString(mm_eff):
    s = '\''
    for i in mm_eff:
            s+='{},'.format(i)
    s = s[:-1]+'\''
    return s

# Input: stdout file
# Output: string of arguments
def get_sim_args(stdout = ''):
	inputs = parse_stdout(stdout)
	param_dict = clean_dict(inputs)
	s = ''
	for key, val in param_dict.items():
		#print(key,val)
		try:
			if key == 'efficiencies':
				s+='{} {} '.format(val[0],formatMMEffString(val[1]))
				continue
			for i in val:
				s+= '{} '.format(i)
		except:
			#print('Parameter {} empty'.format(key))
			continue
	return s


# Argument parser
def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-j",     default=1,        help="Number of jobs to launch")
    parser.add_argument("-i",     default=None,        help="input file")
    parser.add_argument("--run",  action="store_true", help="Enable if you want to run the job")
    return parser.parse_args()


# Main method to launch jobs or get arguments from stdout file
def main():
	ops = options()
	
	if(ops.run):
		print('hi')
		if ops.i:
			if '.txt' in ops.i:
				file = open(ops.i,'r')
				lines = file.readlines()
				for line in lines:
					os.system( " python python/batch_local.py -j {} -a \"{}\" ".format(ops.j,get_sim_args(line.split('\n')[0])))
					time.sleep(1)
			else:
				os.system( " python python/batch_local.py -j {} -a \"{}\" ".format(ops.j,get_sim_args(ops.i)))
		else:
			print("BAD INPUT FILE: {}".format(ops.i))
	else:
		if ops.i:
			if '.txt' in ops.i:
				file = open(ops.i,'r')
				lines = file.readlines()
				for line in lines:
					print(get_sim_args(line.split('\n')[0]))
			else:
				print(get_sim_args(ops.i))
		else:
			print("BAD INPUT FILE: {}".format(ops.i))
		

if __name__ == "__main__":
	main()





