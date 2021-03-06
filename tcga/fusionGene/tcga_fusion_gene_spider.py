#coding=utf-8
import spynner
import urllib2
from BeautifulSoup import BeautifulSoup
import os

'''
get all fusion gene information from TCGA

@ Yanhui Fan (felixfanyh@gmail.com)
last revised on 16 May 2016
'''

'''
根据html的信息计算总页数
'''
def getNumOfPagesFromHtml(html):
	soup = BeautifulSoup(html)
	info = str(soup.find(id="fusions_info"))
	arr = info.split('>')
	ar = arr[1].split('<')
	a = ar[0].split()
	num = a[-2]
	num = int(num.replace(",", ""))
	if num % 10 == 0:
		return num / 10
	else:
		return num / 10 + 1


'''
提取html中fusion gene pair
'''
def extractFusionGenePairsFromHtml(html):
	fgp = []
	# 提取fusion gene pair
	soup = BeautifulSoup(html)
	for link in soup.findAll('a'):
		f_url = link.get('href')
		if f_url and -1 != f_url.find('geneNameA'):
			arr = f_url.split('?')
			fgp.append(arr[1].encode('utf-8'))
	return fgp

'''
提取GCTA数据库里的所有fusion gene pairs
'''
def gcta_spider(cancertype, tierclass):
	browser = spynner.Browser()
	#browser.show()
	browser.hide()

	try:
		browser.load(url='http://54.84.12.177/PanCanFusV2/Fusions!cancerType')
	except spynner.SpynnerTimeout:
		print 'Timeout.'
	else:
		# 输入搜索关键字
		# browser.wk_fill('select[id="cancerType"]', 'BRCA')
		browser.wk_select('[id="cancerType"]', cancertype)

		# browser.wk_fill('select[id="tier"]', 'tier1')
		browser.wk_select('[id="tier"]', tierclass)

		# 点击搜索按钮，并等待页面加载完毕  
		browser.wk_click('input[type="submit"]', wait_load=True)

		# 获取页面的HTML
		html = browser.html

		# get total pages
		pageNum = getNumOfPagesFromHtml(html)

		fusionGenePairs = []

		# first page
		if pageNum > 0:
			p = 1
			print 'processing page %d of %d' % (p, pageNum)
			fusionGenePairs = extractFusionGenePairsFromHtml(html)
		

		# second to last page
		if pageNum > 1:
			for i in xrange(1, pageNum):
				try:
					browser.wk_click('[id="fusions_next"]')
					html = browser.html
					tmp = extractFusionGenePairsFromHtml(html)
					fusionGenePairs.extend(tmp)
					tmp = []
					p = i + 1
					print 'processing page %d of %d' % (p, pageNum)
				except:
					print 'failed to click next page'
					break
				else:
					continue
	browser.close()
	return fusionGenePairs

'''
提取一对fusion gene pairs的注释信息
'''
def getFusionGenePairAnnot(pUrl):
	myurl = "http://54.84.12.177/PanCanFusV2/Fusions!fusion?%s" % pUrl
	soup = BeautifulSoup(urllib2.urlopen(myurl).read())
	annot = []
	for link in soup.findAll('a'):
		if link:
			url = link.get('href')
			if -1 != url.find('Fusion') and url.startswith('details'):
				cancer = url.split('Cancer=')[1].split('&')[0]
				sample = url.split('SampleID=')[1].split('&')[0]
				geneA = url.split('Gene_A=')[1].split('&')[0]
				geneB = url.split('Gene_B=')[1].split('&')[0]
				eValue = url.split('Evalue=')[1].split('&')[0]
				tier = url.split('tier=')[1].split('&')[0]
				frame = url.split('frame=')[1].split('&')[0]
				aChr = url.split('A_chr=')[1].split('&')[0]
				bChr = url.split('B_chr=')[1].split('&')[0]
				aStrand = url.split('A_strand=')[1].split('&')[0]
				bStrand = url.split('B_strand=')[1].split('&')[0]
				juncA = url.split('Junction_A=')[1].split('&')[0]
				juncB = url.split('Junction_B=')[1].split('&')[0]
				Discordant_n	= url.split('Discordant_n=')[1].split('&')[0]
				JSR_n = url.split('&JSR_n=')[1].split('&')[0]
				perfectJSR_n = url.split('perfectJSR_n=')[1].split('&')[0]

				fusionPair = "%s__%s" % (geneA, geneB)
				fivePrimeJunc = "Chr%s:%s/%s" % (aChr, juncA, aStrand)
				threePrimeJunc = "Chr%s:%s/%s" % (bChr, juncB, bStrand)

				tmp = (cancer, sample, geneA, geneB, fusionPair, eValue, tier, frame, fivePrimeJunc, threePrimeJunc, Discordant_n, JSR_n, perfectJSR_n)
				annot.append(tmp)
	return annot

def writeHeader(output):
	print '\nwrite header to %s\n' % output
	header = ("Cancer", "TCGA_Sample_ID", "Gene_A", "Gene_B", "Fusion_Pair", "E_Value", "Tier", "Frame", "5_Prime_Gene_Junction", "3_Prime_Gene_Junction", "Number_of_Discordant_Read _Pair", "Number_of_Junction_Spanning_Read", "Number_of_Perfect_Junction_Spanning_Read")
	f = open(output, 'w')
	f.write(header[0])
	for i in header[1:]:
		f.write('\t%s' % i)
	f.write('\n')
	f.close()

def writeAnnot(output, annot):
	print 'write results to %s' % output
	f = open(output, 'w')
	for i in annot:
		f.write(i[0])
		for j in i[1:]:
			f.write('\t%s' % j)
		f.write('\n')
	f.close()


if __name__ == '__main__':
	# 20 cancers x 4 tiers
	cancertype = ('BLCA', 'BRCA', 'GBM', 'HNSC', 'KIRC', 'LAML', 'LGG', 'LUAD', 'LUSC', 'OV', 'SKCM', 'THCA', 'PRAD', 'ACC', 'UCS', 'CESC', 'ESCA', 'READ', 'UVM','COAD')
	tierclass = ('tier1', 'tier2', 'tier3', 'tier4')

	# test
	# cancertype = ('CESC',)
	# tierclass = ('tier3','tier4') # tier3 -> 2 record, tier4 -> 0 record

	allFusionGenePairs = []

	'''
	add log file to record the process
	so if the connect is break, the program can restart without modify the input
	and the program can start from the breaken point but not from the very beginning.

	log content:
	### cancer tier
	fusion_pair
	'''

	log = 'log.txt'
	fct = [] # finished cancer and finished tier pairs
	if os.path.isfile(log):
		fl = open(log)
		for r in fl:
			r = r.strip()
			if r.startswith('#'):
				arr = r.split()
				fct.append((arr[1],arr[2]))
			else:
				allFusionGenePairs.append(r)
		fl.close()
	fl = open(log, 'a')

	# bye cancer => by tier
	for c in cancertype:
		for t in tierclass:
			if not (c, t) in fct:
				print 'cancer: %s\ttier: %s' % (c, t)
				fgp = gcta_spider(c, t) # fusion gene pair
				l = len(fgp)
				print 'There are total %d fusion gene pair' % l
				if l > 0: # check which pair is already downloaded
					ufgp = []
					for i in fgp:
						if not i in allFusionGenePairs:
							allFusionGenePairs.append(i)
							ufgp.append(i)
					m = len(ufgp)
					if m > 0: # new pair to download
						print 'need to download information for %d pair of fusion genes' % m
						print 'Downloading information for each pair of fusion genes'
						idx = 0
						allAnnot = []
						for ufgpURL in ufgp:
							annot = getFusionGenePairAnnot(ufgpURL)
							allAnnot.extend(annot)
							idx += 1
							if idx % 100 == 1:
								print 'Downloading %d of %d ...' % (idx, m)
						output = 'tcga_fg_%s_%s.txt' % (c, t)
						writeAnnot(output, allAnnot)
						# log
						fl.write('### %s %s\n' % (c, t))
						for z in ufgp:
							fl.write('%s\n' % z)
	fl.close()
	
	# header File
	output = "tcga_fg_annot_header.txt"
	writeHeader(output)

	# cat files
	fl = open(log)
	files = ["tcga_fg_annot_header.txt"]
	for r in fl:
		r = r.strip()
		if r.startswith('#'):
			arr = r.split()
			output = 'tcga_fg_%s_%s.txt' % (arr[1],arr[2])
			files.append(output)
	fl.close()
	print "\nOn Linux or Mac, run the following command to cat all outputs\n"
	comm = ' '.join(files)
	print 'cat ' + comm + ' > tcga_fusionGenes_annot.txt'
