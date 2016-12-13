import os
import re
import sys
from Bio import SeqIO

intermediateFolder = "../Intermediate_Files"
readFolder = "../CCS_Reads"
minCycles = 5
sampleID = "pb16S"
outputfolder = "custom_barcode"

ccsFQ = readFolder+"/"+sampleID+".ccs."+str(minCycles)+"x.fastq"
scraps = intermediateFolder+"/"+sampleID+".scraps.bam"

minLength = 1400
maxLength = 1600

#you can also get barcode information from an SMRT portal aligned .bam file (with RG:Z tag),
#...but you still need to define CCS read

#barcode can be in either subread or scrap, but this script could help add additional reads if otherwise using the ends of the subread for barcode assignments

def demultiplex(ccsFQ, scrapsBam, fastaPrefix, minLength, maxLength):
	scrapsSam = re.sub(".bam",".sam",scrapsBam)

	command = "samtools view " + scrapsBam + " > " +scrapsSam
	#os.system(command)
	
	barcodeHash = {}
	barcodeHash["lbc1"]= "TCAGACGATGCGTCAT"
	barcodeHash["lbc2"]= "CTATACATGACTCTGC"
	barcodeHash["lbc3"]= "TACTAGAGTAGCACTC"
	barcodeHash["lbc4"]= "TGTGTATCAGTACATG"

	#assign ZMW
	zmwHash = {}
	badZmwHash = {}

	inHandle = open(scrapsSam)
	line = inHandle.readline()
	
	while line:
		line = line.replace("\n","")
		line = line.replace("\r","")

		result = re.search("^m",line)	
		if result:
			lineInfo = line.split("\t")
			read =  lineInfo[0]
			zmw = re.sub("\d+_\d+$","",read)
				
			seq = lineInfo[9]
			
			resultB1 = re.search("TCAGACGATGCGTCAT",seq)
			resultB2 = re.search("CTATACATGACTCTGC",seq)
			resultB3 = re.search("TACTAGAGTAGCACTC",seq)
			resultB4 = re.search("TGTGTATCAGTACATG",seq)

			if resultB1 and (not resultB2) and (not resultB3) and (not resultB4):
				if (zmw in zmwHash):
					if zmwHash[zmw] != "lbc1":
						badZmwHash[zmw]=1
				else:
					zmwHash[zmw] = "lbc1"

			if resultB2 and (not resultB1) and (not resultB3) and (not resultB4):
				if (zmw in zmwHash):
					if zmwHash[zmw] != "lbc2":
						badZmwHash[zmw]=1
				else:
					zmwHash[zmw] = "lbc2"
				
			if resultB3 and (not resultB2) and (not resultB1) and (not resultB4):
				if (zmw in zmwHash):
					if zmwHash[zmw] != "lbc3":
						badZmwHash[zmw]=1
				else:
					zmwHash[zmw] = "lbc3"
				
			if resultB4 and (not resultB2) and (not resultB3) and (not resultB1):
				if (zmw in zmwHash):
					if zmwHash[zmw] != "lbc4":
						badZmwHash[zmw]=1
				else:
					zmwHash[zmw] = "lbc4"
			
		line = inHandle.readline()
	
	for zmw in badZmwHash:
		del zmwHash[zmw]
	
	print len(zmwHash.keys())

	#separate reads	
	for barcode in barcodeHash:
		print barcode
		fastaFile = fastaPrefix + "/" + barcode + ".fasta"
		outHandle = open(fastaFile, "w")
		
		fastq_sequences = SeqIO.parse(open(ccsFQ),'fastq')
		for fasta in fastq_sequences:
			readName = fasta.id
			readSequence = str(fasta.seq)

			zmw = re.sub("ccs$","",readName)
			seqLength = len(readSequence)
				
			if (zmw in zmwHash) & (seqLength >= minLength) & (seqLength <= maxLength):
				barcodeAssignment = zmwHash[zmw]
				if barcodeAssignment == barcode:
					text = ">" + read + "\n"
					outHandle.write(text)
						
					text = seq + "\n"
					outHandle.write(text)

demultiplex(ccsFQ, scraps, outputfolder, minLength, maxLength)