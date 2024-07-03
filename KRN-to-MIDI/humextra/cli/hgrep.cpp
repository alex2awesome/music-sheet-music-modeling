//
// Programmer:    Craig Stuart Sapp <craig@ccrma.stanford.edu>
// Creation Date: Sun Apr 19 20:03:05 PDT 2009
// Last Modified: Tue May  4 23:11:52 PDT 2009 Added -t, -c, -B, --sep options
// Last Modified: Tue May  5 09:54:01 PDT 2009 Added -p, -P, --and options
// Last Modified: Mon May 11 20:56:43 PDT 2009 Fix initial beat for comments
// Last Modified: Wed Apr 28 18:49:29 PDT 2010 Added -T and -D options
// Last Modified: Wed Sep 14 10:40:48 PDT 2011 Added -F option
// Last Modified: Sat Apr  6 01:16:22 PDT 2013 Enabled multiple segment input
// Filename:      ...sig/examples/all/hgrep.cpp
// Web Address:   http://sig.sapp.org/examples/museinfo/humdrum/hgrep.cpp
// Syntax:        C++; museinfo
//
// Description:   Grep with Humdrum intelligence built into it.
//

#include <iostream>
#include <fstream>
#include <sstream>

#include <string.h>
#include <math.h>
#include <regex.h>

#include "humdrum.h"

using namespace std;

//////////////////////////////////////////////////////////////////////////

// function declarations:
void      checkOptions        (Options& opts, int argc, char** argv);
void      example             (void);
void      usage               (const string& command);
void      doSearch            (const string& searchstring, HumdrumFile& infile,
                               const string& filename);
void      printPreInfo        (const string& filename, HumdrumFile& infile,
                               double measure, int line, int spine = -1);
char*     searchAndReplace    (char* buffer, const string& searchstring,
                               const string& replacestring,
                               const string& datastring);
void      displayFraction     (double fraction);
void      fillAndSearches     (vector<regex_t>& relist,
                               vector<string>& exlist,
                               const string& string);
int       tokenSearch         (int& column, HumdrumFile& infile, int line,
                               regex_t& re);
int       singleTokenSearch   (int& column, HumdrumFile& infile, int line,
                               regex_t& re, const string& exstring);
void      destroyAndSearches  (vector<regex_t>& relist);
double    getBeatOfNextData   (HumdrumFile& infile, int line);
void      printDitto          (HumdrumFile& infile, int line);
void      markKernNotes       (HumdrumFile& infile, int line);
void      analyzeFile         (HumdrumFile& infile);

// User interface variables:
Options     options;
string      searchstring    = "";    // first argument
int         kernQ           = 0;     // used with -k option
int         dataQ           = 0;     // used with -d option
int         tandemQ         = 0;     // used with -t option
int         commentQ        = 0;     // used with -C option
int         primaryQ        = 0;     // used with -p option
int         nonprimaryQ     = 0;     // used with -P option
int         bibliographicQ  = 0;     // used with -B option
int         absbeatQ        = 0;     // used with -a option
int         fracQ           = 0;     // used with -f option
int         spineQ          = 0;     // used with -s option
int         beatQ           = 0;     // used with -b option
int         measureQ        = 0;     // used with -m option
int         nullQ           = 0;     // used with -n option
int         parenQ          = 1;     // used with -N,-n option
int         quietQ          = 0;     // used with -q option
int         exinterpQ       = 0;     // used with -x option
int         formQ           = 0;     // used with -F option
int         tokenizeQ       = 0;     // used with -T option
int         datastopQ       = 0;     // used with -D option
int         markQ           = 0;     // used with --mark option
string      exinterps       = "";    // used with -x option
char        separator[1024] = {0};   // used with --sep option
vector<regex_t> Andlist;              // used with --and option
vector<string> Andexinterp;     // used with --and option
int         MarkerCount     = 0;
int         MarkerMatchCount= 0;

// standard grep option emulations:
int         fileQ           = 0;     // used with -H option
int         matchfilesQ     = 0;     // used with -l option
int         nomatchfilesQ   = 0;     // used with -L option
int         ignorecaseQ     = 0;     // used with -i option
int         basicQ          = 0;     // used with -G option
int         lineQ           = 0;     // used with -n option
int         invertQ         = 0;     // used with -v option

//////////////////////////////////////////////////////////////////////////

int main(int argc, char** argv) {
	checkOptions(options, argc, argv);
	HumdrumStream streamer(options);
	HumdrumFile infile;

	while (streamer.read(infile)) {
		analyzeFile(infile);
	}

	destroyAndSearches(Andlist);

	return 0;
}



//////////////////////////////
//
// analyzeFile --
//

void analyzeFile(HumdrumFile& infile) {
	if (absbeatQ || beatQ || measureQ || fracQ) {
		// need to do this for measureQ because of pickup information
		infile.analyzeRhythm("4");
	}

	doSearch(searchstring.c_str(), infile, infile.getFilename());
	if (markQ) {
		cout << infile;
		if (MarkerCount) {
			cout << "!!!RDF**kern: @ = marked note ("
					<< MarkerCount << " marks in " << MarkerMatchCount
					<< " matches)" << endl;
			MarkerCount = 0;
			MarkerMatchCount = 0;
		}
	}
}

//////////////////////////////////////////////////////////////////////////


//////////////////////////////
//
// doSearch --
//

void doSearch(const string& searchstring, HumdrumFile& infile,
		const string& filename) {
	regex_t re;
	int flags = 0;
	double measure = 1;
	if (infile.getPickupDur() != 0.0) {
		measure = 0;
	}

	if (!basicQ) {
		flags = flags | REG_EXTENDED;
	}
	if (ignorecaseQ) {
		flags = flags | REG_ICASE;
	}
	int status;
	status = regcomp(&re, searchstring.c_str(), flags);
	if (status != 0) {
		char errstring[1024] = {0};
		regerror(status, &re, errstring, 1000);
		cerr << errstring << endl;
		exit(1);
	}
	int i;
	int matchcount = 0;

	for (i=0; i<infile.getNumLines(); i++) {
		if (datastopQ && infile[i].isData()) {
			break;
		}
		if (formQ && !infile[i].isData()) {
			if (!invertQ) {
				if (nullQ) {
					printDitto(infile, i);
					cout << endl;
				} else {
					cout << infile[i] << endl;
				}
			} else {
				if (strcmp(infile[i][0], "*-") == 0) {
					// handled at marker xyga
				} else if (strncmp(infile[i][0], "**", 2) == 0) {
					// handled at marker xyga
				} else {
					if (nullQ) {
						printDitto(infile, i);
						cout << endl;
					} else {
						cout << infile[i] << endl;
					}
				}
			}
		}

		if (infile[i].isEmpty()) { continue; }
		if (infile[i].isMeasure()) {
			sscanf(infile[i][0],"=%lf", &measure);
		}
		if (dataQ && tandemQ) {
			if (!(infile[i].isData() || infile[i].isTandem())) { continue; }

		} else {
			if (dataQ && (!infile[i].isData())) { continue; }
			if (tandemQ && (!infile[i].isTandem())) { continue; }
		}
		if (commentQ && (!infile[i].isComment())) { continue; }
		if (bibliographicQ && (!infile[i].isBibliographic())) { continue; }

		if (exinterpQ || kernQ) {
			if (!(infile[i].isData() || infile[i].isInterpretation() ||
					infile[i].isMeasure() || infile[i].isLocalComment())) {
				continue;
			}
			int column = -1;
			status = tokenSearch(column, infile, i, re);
			// status == 0 means a match was found
			// status != 0 means a match was not found
			if (markQ && !status) {
				markKernNotes(infile, i);
				continue;
			}

			if (invertQ) {
				status = !status;
			}
			if (status == 0) {
				matchcount++;
				if (matchfilesQ) {
					cout << filename << endl;
					return;
				}
				if (nomatchfilesQ) {
					continue;
				}
				printPreInfo(filename, infile, measure, i, column);
				if (!quietQ) {
					// marker xyga
					if (nullQ) {
						printDitto(infile, i);
					} else {
						cout << infile[i];
					}
				}
				cout << endl;
			}

		} else { // search entire line as a single unit
			if (tokenizeQ) {
				status = 0;
				for (int ii=0; ii<infile[i].getFieldCount(); ii++) {
					status = tokenSearch(ii, infile, i, re);
					if (markQ && !status) {
						markKernNotes(infile, i);
						continue;
					}
					if (status == 0) {
						break;
					}
				}
			} else {
				status = regexec(&re, infile[i].getLine(), 0, NULL, 0);
				if (markQ && !status) {
					markKernNotes(infile, i);
					continue;
				}
			}
			if (Andlist.size() > 0) {
				for (int aa=0; aa<(int)Andlist.size(); aa++) {
					int newstatus = regexec(&Andlist[aa], infile[i].getLine(),
							0, NULL, 0);
					if (newstatus != 0) {
						status = 1;
					}
				}
			}
			if (invertQ) {
				status = !status;
			}
			if (status == 0) {
				matchcount++;
				if (matchfilesQ) {
					cout << filename << endl;
					return;
				}
				if (nomatchfilesQ) {
					continue;
				}
				printPreInfo(filename, infile, measure, i, -1);
				if (!quietQ) {
					if (nullQ) {
						printDitto(infile, i);
					} else {
						cout << infile[i];
					}
				}
				cout << endl;
			}

		}
	}

	regfree(&re);
	if (nomatchfilesQ && matchcount == 0) {
		cout << filename << endl;
	}
}



//////////////////////////////
//
// markKernNotes -- Read across the line and mark all notes with '@' which
// occur on that line, or resolve the null tokens to mark previous notes
// which are currently sounding.
//

void markKernNotes(HumdrumFile& infile, int line) {
	int j;
	if (!infile[line].isData()) {
		return;
	}
	MarkerMatchCount++;
	char buffer[1024] = {0};
	HumdrumFileAddress add;
	for (j=0; j<infile[line].getFieldCount(); j++) {
		if (!infile[line].isExInterp(j, "**kern")) {
			continue;
		}
		add.setLineField(line, j);
		infile.getNonNullAddress(add);
		if (strchr(infile[add], 'r') != NULL) {
			continue;
		}
		if (strchr(infile[add], '@') != NULL) {
			// don't duplicate @ marker in a token
			continue;
		}
		MarkerCount++;
		strcpy(buffer, infile[add]);
		strcat(buffer, "@");
		infile.changeField(add, buffer);
	}
}



//////////////////////////////
//
// printDitto -- fill in null tokens with/without parentheses
//

void printDitto(HumdrumFile& infile, int line) {
	int j, ii, jj;
	if (!infile[line].isData()) {
		cout << infile[line] << endl;
	}
	int count = infile[line].getFieldCount();
	int null = 0;
	for (j=0; j<count; j++) {
		ii = line;
		jj = j;
		null = 0;
		if (strcmp(infile[ii][jj], ".") == 0) {
			ii = infile[line].getDotLine(j);
			jj = infile[line].getDotSpine(j);
			null = 1;
		}
		if (null && parenQ) {
			cout << "(" << infile[ii][jj] << ")";
		} else {
			cout << infile[ii][jj];
		}
		if (j<count-1) {
			cout << '\t';
		}
	}
}



//////////////////////////////
//
// singleTokenSearch -- used in tokenSearch, but only doing one search
//   on a line at a time.  Returns 0 if a match was found, otherwise
//   returns 1 (or a non-zero) if no match.
//

int singleTokenSearch(int& column, HumdrumFile& infile, int line, regex_t& re,
		const string& exstring) {
	int status;
	for (int j=0; j<infile[line].getFieldCount(); j++) {
		if (exstring.size() == 0) {
			// don't filter out based on exclusive interpretation types
		} else if (exstring.find(infile[line].getExInterp(j)) == std::string::npos) {
			continue;
		}

		if ((infile[line].getSpineInfo(j).find('b') != std::string::npos) ||
				(infile[line].getSpineInfo(j).find("((") != std::string::npos)) {
			if (primaryQ) {
				continue;
			}
		} else {
			if (nonprimaryQ) {
				continue;
			}
		}

		status = regexec(&re, infile[line][j], 0, NULL, 0);
		if (status == 0) {
//cout << "AND MATCH FOUND IN TOKEN: " << infile[line][j] << endl;
//cout << "USING REGEX " << (int)(&re) << endl;
			return status;
		}
	}

	return 1; // no match was found on the line
}



//////////////////////////////
//
// tokenSearch -- returns 0 if a match was found, otherwise returns 1
//      if no match was found.
//
//

int tokenSearch(int& column, HumdrumFile& infile, int line, regex_t& re) {
	int matchfound = 0;

	if (kernQ) {
		matchfound = singleTokenSearch(column, infile, line, re, "**kern");
	} else {
		matchfound = singleTokenSearch(column, infile, line, re, exinterps.c_str());
	}

	if (matchfound != 0) {
		return matchfound;
	}

	if (Andlist.size() == 0) {
		return matchfound;
	}

//cout << "CHECKING AND DATA" << endl;
	for (int i=0; i<(int)Andlist.size(); i++) {
		if (kernQ && Andexinterp[i].empty()) {
			matchfound = singleTokenSearch(column, infile, line,
					Andlist[i], "**kern");
		} else {
			matchfound = singleTokenSearch(column, infile, line,
					Andlist[i], Andexinterp[i]);
		}
		if (matchfound != 0) {
			column = -1;  // don't identify spine for anded searches
			return 1;
		}
	}

	column = -1;  // don't identify spine for anded searches
	return 0; // all matches were satisfied
}



//////////////////////////////
//
// searchAndReplace --
//

char* searchAndReplace(char* buffer, const string& searchstring,
		const string& replacestring, const string& datastring) {
	buffer[0] = '\0';
	regex_t re;
	regmatch_t match;
	int compflags = 0;
	if (!basicQ) {
		compflags = compflags | REG_EXTENDED;
	}
	if (ignorecaseQ) {
		compflags = compflags | REG_ICASE;
	}
	int status = regcomp(&re, searchstring.c_str(), compflags);
	if (status !=0) {
		regerror(status, &re, buffer, 1024);
		cerr << buffer << endl;
		exit(1);
	}
	const char* dstring = datastring.c_str();
	status = regexec(&re, dstring, 1, &match, 0);
	while (status == 0) {
		strncat(buffer, dstring, match.rm_so);
		strcat(buffer, replacestring.c_str());
		dstring += match.rm_eo;
		status = regexec(&re, dstring, 1, &match, REG_NOTBOL);
	}
	strcat(buffer, dstring);
	regfree(&re);
	return buffer;
}




//////////////////////////////
//
// printPreInfo --
//    default value: spine = -1
//

void printPreInfo(const string& filename, HumdrumFile& infile, double measure,
		int line, int spine) {
	if (fileQ) {
		cout << filename << separator;
	}
	if (lineQ) {
		cout << "line " << line+1 << separator;
	}
	if (spineQ && (spine >= 0)) {
		cout << "spine " << spine+1 << separator;
	} /* else if (spineQ) {
		cout << "spine " << 1 << separator;
	} */

	if (measureQ) {
		cout << "measure " << measure << separator;
	}
	if (beatQ) {
		if (infile[line].getBeat() == 0.0) {
			cout << "beat " << getBeatOfNextData(infile, line) << separator;
		} else {
			cout << "beat " << infile[line].getBeat() << separator;
		}
	}
	if (absbeatQ) {
		cout << "absbeat " << infile[line].getAbsBeat() << separator;
	}
	if (fracQ) {
		cout << "frac ";
		displayFraction(infile[line].getAbsBeat()/infile.getTotalDuration());
		cout << separator;
	}
}



//////////////////////////////
//
// getBeatOfNextData -- used to fix the beat position of comments
//      at the start of measures which would be labeled as
//      beat 0 instead of beat 1.
//

double getBeatOfNextData(HumdrumFile& infile, int line) {
	int i;
	double output = infile[line].getBeat();
	for (i=line; i<infile.getNumLines(); i++) {
		if ((!infile[i].isData()) && (!infile[i].isMeasure())) {
			continue;
		}
		output = infile[i].getBeat();
		break;
	}

	return output;
}



//////////////////////////////
//
// displayFraction
//

void displayFraction(double fraction) {
	int value;
	if (fraction == 0.0) {
		cout << "0.000";
	} else if (fraction == 1.0) {
		cout << "1.000";
	} else if (fraction > 0.0 && fraction < 1.0) {
		value = int(fraction * 1000.0 + 0.5);
		cout << "0.";
		if (value < 100) { cout << "0"; }
		if (value < 10) { cout << "0"; }
		cout << value;
	} else {
		cout << fraction;
	}
}



//////////////////////////////
//
// checkOptions --
//

void checkOptions(Options& opts, int argc, char* argv[]) {

	opts.define("a|absbeat=b",  "display the absolute beat postion of a match");
	opts.define("b|beat=b",     "display the metrical beat postion of a match");
	opts.define("B|bibliographic=b", "search only bibliographic records");
	opts.define("C|comment=b",       "search only comment records");
	opts.define("d|data=b",          "search only data records");
	opts.define("f|fraction|frac=b", "disp. pos. as fraction of total length");
	opts.define("F|form=b",          "preserve Humdrum file formattting");
	opts.define("k|kern=b",          "search only **kern records");
	opts.define("p|primary=b",       "search only primary spines");
	opts.define("P|nonprimary=b",    "search only non-primary spines");
	opts.define("q|quiet=b", "don't display matching lines (just pre markers)");
	opts.define("t|tandem=b",        "search only data records");
	opts.define("s|spine=b",         "display spine number of match");
	opts.define("m|measure=b",       "display measure number of match");
	opts.define("N|null|ditto=b",    "resolve null tokens like ditto command");
	opts.define("x|exinterp=s",      "search only listed exinterps");
	opts.define("T|tokenize=b",      "search tokens independently");
	opts.define("mark=b",            "mark notes on data lines that match");
	opts.define("D|data-stop=b",     "stop search at first data record");
	opts.define("sep|separator=s::", "data separator string");
	opts.define("no-paren=b",        "don't display null parentheses");
	opts.define("and=s:",            "anded search strings");

	// options which mimic regular grep program:
	opts.define("G|basic-regexp=b",  "use basic regular expression syntax");
	opts.define("H|with-filename=b",  "display filename at start match line");
	opts.define("h|no-filename=b","do not display filename on match line");
	opts.define("L|files-without-match=b", "list files without match");
	opts.define("l|files-with-match=b", "list files with match(es)");
	opts.define("i|ignore-case=b", "ignore case in matches");
	opts.define("n|line-number=b", "display line number of match");
	opts.define("v|invert-match=b", "invert the matching criteria");

	opts.define("author=b",  "author of program");
	opts.define("version=b", "compilation info");
	opts.define("example=b", "example usages");
	opts.define("help=b",  "short description");
	opts.process(argc, argv);

	// handle basic options:
	if (opts.getBoolean("author")) {
		cout << "Written by Craig Stuart Sapp, "
			  << "craig@ccrma.stanford.edu, April 2009" << endl;
		exit(0);
	} else if (opts.getBoolean("version")) {
		cout << argv[0] << ", version: 3 May 2018" << endl;
		cout << "compiled: " << __DATE__ << endl;
		cout << MUSEINFO_VERSION << endl;
		exit(0);
	} else if (opts.getBoolean("help")) {
		usage(opts.getCommand().c_str());
		exit(0);
	} else if (opts.getBoolean("example")) {
		example();
		exit(0);
	}

	if (opts.getArgCount() < 1) {
		cerr << "Error: you must supply a search string\n";
		exit(1);
	}
	searchstring  =  opts.getArg(1);
	basicQ        =  opts.getBoolean("basic-regexp");
	fileQ         =  opts.getBoolean("with-filename");
	matchfilesQ   =  opts.getBoolean("files-with-match");
	nomatchfilesQ =  opts.getBoolean("files-without-match");
	ignorecaseQ   =  opts.getBoolean("ignore-case");
	lineQ         =  opts.getBoolean("line-number");
	invertQ       =  opts.getBoolean("invert-match");

	absbeatQ      =  opts.getBoolean("absbeat");
	beatQ         =  opts.getBoolean("beat");
	quietQ        =  opts.getBoolean("quiet");
	kernQ         =  opts.getBoolean("kern");
	fracQ         =  opts.getBoolean("fraction");
	dataQ         =  opts.getBoolean("data");
	tandemQ       =  opts.getBoolean("tandem");
	primaryQ      =  opts.getBoolean("primary");
	commentQ      =  opts.getBoolean("comment");
	nonprimaryQ   =  opts.getBoolean("nonprimary");
	bibliographicQ=  opts.getBoolean("bibliographic");
	spineQ        =  opts.getBoolean("spine");
	formQ         =  opts.getBoolean("form");
	measureQ      =  opts.getBoolean("measure");
	nullQ         =  opts.getBoolean("ditto");
	parenQ        = !opts.getBoolean("no-paren");
	tokenizeQ     =  opts.getBoolean("tokenize");
	datastopQ     =  opts.getBoolean("data-stop");
	markQ         =  opts.getBoolean("mark");
	exinterpQ     =  opts.getBoolean("exinterp");
	exinterps     =  opts.getString("exinterp").c_str();
	char tempbuffer[1024] = {0};
	searchAndReplace(tempbuffer, "[\\]t", "	", opts.getString("separator").c_str());
	searchAndReplace(separator, "[\\]n", "\n", tempbuffer);

	if (matchfilesQ && nomatchfilesQ) {
		nomatchfilesQ = 0;
	}

	Andlist.resize(0);
	Andexinterp.resize(0);
	if (opts.getBoolean("and")) {
		fillAndSearches(Andlist, Andexinterp, opts.getString("and").c_str());
	}
}



//////////////////////////////
//
// fillAndSearches -- exinterp strings are sticky.
//

void fillAndSearches(vector<regex_t>& relist, vector<string>& exlist,
		const string& astring) {
	char* buffer;
	int bufsize = (int)astring.size() * 2 + 128;
	buffer = new char[bufsize];
	for (int i=0; i<bufsize; i++) {
		buffer[i] = '\0';
	}
	relist.reserve(100);
	relist.resize(0);

	char exbuff[1024] = {0};

	int status;
	int compflags = 0;
	if (!basicQ) {
		compflags = compflags | REG_EXTENDED;
	}
	if (ignorecaseQ) {
		compflags = compflags | REG_ICASE;
	}

	searchAndReplace(buffer, "[\\]n", "\n", astring);
	char* ptr = strtok(buffer, "\n");
	while (ptr != NULL) {

		if (strncmp("**", ptr, 2) == 0) {
			strcpy(exbuff, ptr);
			ptr = strtok(NULL, "\n");
			continue;
		}
		relist.resize(relist.size()+1);
//cout << "SEARCH STRING ADDED: " << ptr << endl;
//cout << "ADDRESS IS " << (int)(&(relist[relist.size()-1])) << endl;
		status = regcomp(&(relist[(int)relist.size()-1]), ptr, compflags);
		if (status !=0) {
			regerror(status, &(relist[(int)relist.size()-1]), buffer, 1024);
			cerr << buffer << endl;
			exit(1);
		}
		exlist.push_back(exbuff);
		ptr = strtok(NULL, "\n");
	}
	delete [] buffer;
}



//////////////////////////////
//
// destroyAndSearches --
//

void destroyAndSearches(vector<regex_t>& relist) {
	for (int i=0; i<(int)relist.size(); i++) {
		regfree(&(relist[i]));
	}
	relist.resize(0);
}



//////////////////////////////
//
// example --
//

void example(void) {


}



//////////////////////////////
//
// usage --
//

void usage(const string& command) {

}



