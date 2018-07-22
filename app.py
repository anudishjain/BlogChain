# to implement the hashing using SHA256 we use the HASHLIB and to get the JSON object data from the classes we use the JSON class
# time module is used to create the timestamps in the blocks

''' any Transaction here is defined as the post made by a contributor, it is like a BLOG based on BLOKCHAIN

any POST on this blockchain can be replaced with the term DATA

Blog Posts / Transactions by the user are defined using JSON format

{
"author" : "Anudish Jain",
"post" : "Welcome to BLOG-CHAIN"
"timestamp" : "6 July '18"
}

'''

# Block - Structure (the block is the unit of blockchain which is collection of several transactions)

class Block:

	def __init__(self, index, transactions, timestamp, previous_hash) :

		self.index = index
		self.transactions = transactions
		self.timestamp = timestamp
		self.previous_hash = previous_hash

		# previous hash is used to create the chain of the blocks as each new block is generated with the help of the hash of the previous block
		# this defines the constructor used to initialize the object of the BLOCK, each BLOCK has an index for it's unique identification
		# list of transactions and the timestamp of its creation


	def getBlock_Hash(self) :

		json_data_of_block = json.dumps(self.__dict__, sort_keys = True)
		return sha256(json_data_of_block.encode()).hexdigest()

		'''
		json.dumps is used to transfer the object data to a file or network streams

		we want to convert the dictionary to a string using json.dumps
		we are encoding the python dictionary here to JSON

		to dump the JSON into a file/socket or whatever, then you should go for dump(). If you only need it as a string (for printing, 
		parsing or whatever) then use dumps()
		'''

# Blockchain Class - Collection of Blocks and defines the Connections between the Blocks

class Blockchain:

	difficulty = 2
	# difficulty defines the amount of leading zeroes that are appended in front of the calculated hash -- Concept of POW Algo

	def create_genesis_block(self) :

		genesis_block = Block(0, [], time.time(), "0")
		# data stored in the GENESIS BLOCK - User Dependent data -- genesis block has no previous hash -- set as '0'
		genesis_block.hash = genesis_block.getBlock_Hash()
		# get the hash of this BLOCK as it will be used to create --- previous_hash parameter oof the next block
		self.chain.append(genesis_block)
		# as the genesis block is not to be verified we append it to the main blockchain directly

	def __init__(self) :

		self.unconfirmed_transactions = []
		# list of the transactions that are yet to be confirmed

		self.chain = []
		# the main blockchain of transactions / posts, only confirmed transactions are appended are here

		self.create_genesis_block()
		# function to create the GENESIS BLOCK as soon as blockchain is initialized


	#### ------- SUPER IMPORTANT --------
	@property
	def last_block(self):
		return self.chain[-1]

	# @property is shortcut for creating readonly properties

	# now whenever we write Blockchain.last_block and not Blockchain.last_block() we will have the latest added block of the BLOCKCHAIN
	# chain[-1] = chain[chain.size() - 1]

	# by using @ property here we ensure the user is able to access the last block from the chain but cannot mutate it as it is READ-ONLY
	# by @property we cannot directly access the last_block properties of this class



	# ------------  PROOF OF WORK ALGORITHM ------------
	#### ---------------- SUPER IMPORTANT ---------------
	def proof_of_work(self, block) :

		block.nonce = 0	# nonce is used to increase the difficulty of computing the hash and make it a more random process
		hash_block = block.getBlock_Hash()

		while not hash_block.startswith('0' * Blockchain.difficulty) :

			# till the time our block_hash is not having TWO 0's in front we keep on increasing the nonce of the block
			# as the hash is random process we don't know how many nonces will pass till we get TWO 0's in front of our hash

			# hence we have placed a condition on our HASH_GENERATION process of the blocks

			# a nonce can be defined only once and thus ensures the safety and immutablility of BLOCKCHAIN

			block.nonce += 1
			hash_block = block.getBlock_Hash()

		return hash_block


	# -------- Adding Blocks to the Blockchain after Verification ---------
	def add_block(self, block, proof) :

		previous_hash = self.last_block.hash
		# previous_hash variable holds the hash of the latest block added ( returned by the @property decorator )

		if previous_hash != block.previous_hash :
			return False
			# checking if previous hash contained in the block and the one we got from the decorator are same

		if not self.is_valid_proof(block, proof) :
			return False

		block.hash = proof
		self.chain.append(block)

		# if all conditions are met we place the 'proof' as the hash of the new block created and append it in the Blockchain
		return True



	def is_valid_proof(self, block, block_hash) :

		return ((block_hash.startswith('0' * Blockchain.difficulty)) and (block_hash == block.getBlock_Hash())) # must satisfy BOTH

		# the block satisifies the condition of the TWO leading zeroes in it's hash
		# and, the transmitted hash is same as the hash of the transmitted block


	# -------- Mining of Blockchain ---------

	def add_new_transactions(self, transactions) :

		self.unconfirmed_transactions.append(transactions)
		# appending the new transactions waiting to get confirmed


	def mine(self) :

		if not self.unconfirmed_transactions : # i.e. no unconfirmed transactions to mine
			return False

		last_block = self.last_block # got the latest block from @property decorator

		new_block = Block(index = last_block.index + 1, transactions = self.unconfirmed_transactions,
		timestamp = time.time(), previous_hash = last_block.hash)

		# creating the new_block having all the unconfirmed_transactions contained in it

		proof = self.proof_of_work(new_block)
		# implementing the proof of work which returns the hash of the new block added

		self.add_block(new_block, proof)
		# adding this block to the blockchain

		self.unconfirmed_transactions = []
		# and as we have placed all unconfirmed transactions in this block we make it empty once again

		announce_block(new_block)

		return new_block.index
		# returns the index of the new block


''' ----------------------------------------------------------------------------'''

from hashlib import sha256
import json
import time

from flask import *
import requests


app = Flask(__name__)
app.secret_key = 'abdhwifvyevekvj72434343vdbytnyjy121'
blockchain = Blockchain()


peers = set()
# contains the list to all the peers of the network i.e. all the other nodes

def consensus() :

	''' Consensus Algorithm :

	As we have multiple nodes in the network to ensure that the copy of blockchain is valid for different nodes we check the copies 
	using this algorithm and select the longest chain as it shows the most amount of work done 

	Even if a node tries to maipulate it's own copy seeing that the system will update all copies with his malicious copy is not posssible due to this algo
	this ensure that all the copies of blockchain across the system are valid and error free '''

	global blockchain

	longest_chain = None

	current_length = len(blockchain)

	for node in peers :

		response = requests.get('http://{}/chain'.format(node))
		length = response.json()['length']
		chain = response.json()['chain']

		if len > current_length and blockchain.check_chain_valid(chain) :

			current_length = len
			longest_chain = chain

	if longest_chain :

		blockchain = longest_chain
		return True

	return False


def announce_block(block) :
		
	for peer in peers :

		url = 'http://{}/add_block'.format(peer)
		requests.post(url, data = json.dumps(block.__dict__, sort_keys = True))



@app.route('/') 
def home() :
	return render_template('index.html')


# ---- Route to enter New Post in the Blog
@app.route('/new_transactions', methods=['POST'])
def new_transactions():

	author = request.form.get('author')
	post = request.form.get('post')

	if not author or not post :
		return 'Invalid Data Transactions', 404

	tx_data = {}

	tx_data['author'] = author
	tx_data['post'] = post

	blockchain.add_new_transactions(tx_data)

	return redirect(url_for('pending_tx'))

# ---- Route to return the whole blockchain
@app.route('/chain', methods=['GET'])
def chain():
	chain_data = []

	for block in blockchain.chain:
		chain_data.append(block.__dict__)

	return render_template('blockchain_posts.html', posts = chain_data)

# dumping the string form of the python object to the user with chain_length


# ---- Mining Route
@app.route('/mine', methods=['GET'])
def mine():
	result = blockchain.mine()
	# get the mining result

	return render_template('mine.html', message = result)


# ---- Get unconfirmed_transaction
@app.route('/pending_tx')
def pending_tx():

	return render_template('pending_transact.html', collect = blockchain.unconfirmed_transactions)


# ------------- decentralizing our blockchain -- bringing multiple nodes in the system ----


@app.route('/add_nodes' , methods = ['POST'])
def register_new_node() :
		
	nodes = request.form.get('add_node')

	if not nodes :
		return "Invalid Data", 404

	peers.add(nodes)
		# if valid data is provided then we add them as nodes to the network

	return "Success", 202


# route to tell other nodes that a new block is mined so that they can update their copies and move on to mine next blocks
@app.route('/add_block' , methods=['POST'])
def validate_and_add() :

	block_data = request.get_json()
	block = Block(block_data["index"], block_data["transactions"], block_data["timestamp"], block_data["previous_hash"])
	proof = block_data['hash']
	added = add_block(block, proof)

	if not added :
		return "The block was discarded by the nodes", 400

	return "Block has been added successfully", 201
	
	#The announce_new_block method should be called after every block is mined by the node, so that peers
	#can add it to their chains.

@app.route('/new_node')
def add_nodes() :

	return render_template('add_node.html')

# --------------------------------------

app.run()


