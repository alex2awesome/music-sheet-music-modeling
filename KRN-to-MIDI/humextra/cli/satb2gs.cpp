//
// Programmer:    Craig Stuart Sapp <craig@ccrma.stanford.edu>
// Creation Date: Sun Feb  6 14:33:36 PST 2011
// Last Modified: Sun Feb  6 14:33:39 PST 2011
// Filename:      ...sig/examples/all/satb2gs.cpp
// Web Address:   http://sig.sapp.org/examples/museinfo/humdrum/satb2gs.cpp
// Syntax:        C++; museinfo
//
// Description:   Converts Soprano/Alto/Tenor/Bass staves into
//                Grand-staff style.
//

#include <iostream>
#include <sstream>

#include <math.h>
#include <time.h>    /* for current time/date */
#include <string.h>

#include "humdrum.h"
#include "PerlRegularExpression.h"

using namespace std;

//////////////////////////////////////////////////////////////////////////

// function declarations:
void  checkOptions             (Options& opts, int argc, char** argv);
void  example                  (void);
void  usage                    (const char* command);
void  convertData              (HumdrumFile& infile);
int   getSatbTracks            (vector<int>& tracks, HumdrumFile& infile);
void  printSpine               (HumdrumFile& infile, int row, int col,
                                vector<int>& satbtracks);
void  printExInterp            (HumdrumFile& infile, int line,
                                vector<int>& tracks);
void  printLastLine            (HumdrumFile& infile, int line,
                                vector<int>& tracks);

// User interface variables:
Options options;
int    debugQ    = 0;             // used with --debug option

//////////////////////////////////////////////////////////////////////////

int main(int argc, char** argv) {
	checkOptions(options, argc, argv);
	HumdrumStream streamer(options);
	HumdrumFile infile;

	while (streamer.read(infile)) {
		convertData(infile);
	}

	return 0;
}


//////////////////////////////////////////////////////////////////////////


//////////////////////////////
//
// convertData -- data is assumed to be in the order from
// bass, tenor, alto, soprano, with non-**kern data found
// in any order.  Only the first four **kern spines in the file
// will be considered.
//

void convertData(HumdrumFile& infile) {
	vector<int> satbtracks(4);
	int exinterpline = getSatbTracks(satbtracks, infile);
	int i, j;
	int lastline = -1;
	for (i=0; i<exinterpline; i++) {
		cout << infile[i] << endl;
	}

	printExInterp(infile, exinterpline, satbtracks);

	for (i=exinterpline+1; i<infile.getNumLines(); i++) {
		if (infile[i].getFieldCount() == 1) {
			cout << infile[i] << endl;
			continue;
		}
		if (strcmp(infile[i][0], "*-") == 0) {
			lastline = i;
			break;
		}
		for (j=0; j<infile[i].getFieldCount(); j++) {
			printSpine(infile, i, j, satbtracks);
			if (j < infile[i].getFieldCount() - 1) {
				cout << '\t';
			}
		}
		cout << '\n';
	}

	if (lastline < 0) {
		return;
	}
	printLastLine(infile, lastline, satbtracks);

	for (i=lastline+1; i<infile.getNumLines(); i++) {
		cout << infile[i] << endl;
	}
}


//////////////////////////////
//
// printLastLine --
//

void printLastLine(HumdrumFile& infile, int line, vector<int>& tracks) {
	int track;
	stringstream output;
	for (int j=0; j<infile[line].getFieldCount() - 1; j++) {
		track = infile[line].getPrimaryTrack(j);
		if ((track == tracks[1]) || (track == tracks[3])) {
			continue;
		}
		if (track == tracks[0])  {
			output << "*v\t*v";
		} else if (track == tracks[2])  {
			output << "*\t*";
		} else {
			output << "*";
		}
		output << "\t";
	}

	output << ends;
	string strang = output.str();
	PerlRegularExpression pre;
	pre.sar(strang, "\t+$", "", "");
	cout << strang;
	cout << endl;

	stringstream output2;
	for (int j=0; j<infile[line].getFieldCount() - 1; j++) {
		track = infile[line].getPrimaryTrack(j);
		if ((track == tracks[1]) || (track == tracks[3])) {
			continue;
		}
		if (track == tracks[2])  {
			output2 << "*v\t*v";
		} else if (track == tracks[0])  {
			output2 << "*";
		} else {
			output2 << "*";
		}
		output2 << "\t";
	}

	output2 << ends;
	strang = output2.str();
	pre.sar(strang, "\t+$", "", "");
	cout << strang;
	cout << endl;

	for (int j=0; j<infile[line].getFieldCount()-2; j++) {
		cout << infile[line][j];
		if (j < infile[line].getFieldCount() - 3) {
			cout << "\t";
		}
	}
	cout << "\n";

}



//////////////////////////////
//
// printExInterp -- print only tenor and soprano tracks
//

void printExInterp(HumdrumFile& infile, int line, vector<int>& tracks) {
	stringstream output;
	int j;
	int track;


	// first print exclusive interpretations
	for (j=0; j<infile[line].getFieldCount(); j++) {
		track = infile[line].getPrimaryTrack(j);
		if ((track == tracks[1]) || (track == tracks[3])) {
			continue;
		}
		output << infile[line][j] << "\t";
	}
	string strang;
	output << ends;
	strang = output.str();
	PerlRegularExpression pre;
	pre.sar(strang, "\t+$", "");
	cout << strang;
	cout << endl;

	stringstream output2;
	stringstream output3;
	for (j=0; j<infile[line].getFieldCount(); j++) {
		track = infile[line].getPrimaryTrack(j);
		if ((track == tracks[1]) || (track == tracks[3])) {
			continue;
		}
		if (track == tracks[0]) {
			output3 << "*clefF4";
			output2 << "*^";
		} else if (track == tracks[2]) {
			output3 << "*clefG2";
			output2 << "*^";
		} else {
			output3 << "*";
			output2 << "*";
		}
		output3 << "\t";
		output2 << "\t";
	}

	output3 << ends;
	strang = output3.str();
	pre.sar(strang, "\t+$", "", "");
	cout << strang;
	cout << endl;

	output2 << ends;
	strang = output2.str();
	pre.sar(strang, "\t+$", "", "");
	cout << strang;
	cout << endl;

}



///////////////////////
//
// printSpine --
//

void printSpine(HumdrumFile& infile, int row, int col, vector<int>& satbtracks) {
	int track = infile[row].getPrimaryTrack(col);
	int j, k;
	int target = -1;
	for (k=0; k<(int)satbtracks.size(); k++) {
		if (track == satbtracks[k]) {
			if (k % 2 == 0) {
				target = satbtracks[k+1];
			} else {
				target = satbtracks[k-1];
			}
			break;
		}
	}

	if (target < 0) {
		// does not need to be switched
		cout << infile[row][col];
		return;
	}

	// print the SAT or B token(s) (there should be only one token for each)
	//
	// If a tenor has a fermata and a bass has a fermata and both are
	// the same duration, then hide the tenor's fermata.
	//
	// If an alto has a fermata and a soprano has a fermata and both are
	// the same duration, then hide the alto's fermata.
	//


	// first identify the column for each voice, considering only the first
	// layer, if there are multiple layers.
	vector<int> cols(4, -1);
	for (j=0; j<infile[row].getFieldCount(); j++) {
		track = infile[row].getPrimaryTrack(j);
		for (k=0; k<(int)satbtracks.size(); k++) {
			if (cols[k] >= 0) {
				continue;
			}
			if (track == satbtracks[k]) {
				cols[k] = j;
			}
		}
	}

	PerlRegularExpression pre;
	string strang;
	int count = 0;
	for (j=0; j<infile[row].getFieldCount(); j++) {
		track = infile[row].getPrimaryTrack(j);
		if (track == target) {
			if (count > 0) {
				cout << '\t';
			}
			strang = infile[row][j];
			pre.sar(strang, "^\\*clef", "!*clef", "");

			if (infile[row].isData()) {

				if ((cols[0] == col) && (strchr(infile[row][col], ';') != NULL)) {
					RationalNumber tenordur;
					RationalNumber bassdur;
					tenordur = Convert::kernToDurationR(infile[row][cols[0]]);
					bassdur  = Convert::kernToDurationR(infile[row][cols[1]]);
					if (tenordur == bassdur) {
						pre.sar(strang, ";", ";y", "g"); // hide fermata
					}
				}

				if ((cols[3] == col) && (strchr(infile[row][col], ';') != NULL)) {
					RationalNumber altodur;
					RationalNumber sopranodur;
					altodur = Convert::kernToDurationR(infile[row][cols[3]]);
					sopranodur  = Convert::kernToDurationR(infile[row][cols[2]]);
					if (altodur == sopranodur) {
						pre.sar(strang, ";", ";y", "g"); // hide fermata
					}
				}

			}

			cout << strang;
			count++;
		}
	}
}



///////////////////////////////
//
// getSatbTracks -- return the primary track numbers of the satb spines.
//
//

int getSatbTracks(vector<int>& tracks, HumdrumFile& infile) {
	int i, j;
	int output = -1;
	tracks.resize(0);
	int track;
	for (i=0; i<infile.getNumLines(); i++) {
		if (!infile[i].isInterpretation()) {
			continue;
		}
		output = i;
		for (j=0; j<infile[i].getFieldCount(); j++) {
			if (!infile[i].isExInterp(j, "**kern")) {
				continue;
			}
			track = infile[i].getPrimaryTrack(j);
			tracks.push_back(track);
			if (tracks.size() == 4) {
				return output;
			}
		}
		break;
	}

	if (tracks.size() != 4) {
		cerr << "Error: there are only " << tracks.size() << " **kern spines"
			  << " in input data" << endl;
		exit(1);
	}

	return output;
}



//////////////////////////////
//
// checkOptions --
//

void checkOptions(Options& opts, int argc, char** argv) {
	opts.define("d|debug=b",    "Debugging information");

	opts.define("author=b",    "Program author");
	opts.define("version=b",   "Program version");
	opts.define("example=b",   "Program examples");
	opts.define("h|help=b",    "Short description");
	opts.process(argc, argv);

	// handle basic options:
	if (opts.getBoolean("author")) {
		cout << "Written by Craig Stuart Sapp, "
			  << "craig@ccrma.stanford.edu, Feb 2011" << endl;
		exit(0);
	} else if (opts.getBoolean("version")) {
		cout << argv[0] << ", version: 5 Feb 2011" << endl;
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

	debugQ =  opts.getBoolean("debug");
}



//////////////////////////////
//
// example -- example function calls to the program.
//

void example(void) {


}



//////////////////////////////
//
// usage -- command-line usage description and brief summary
//

void usage(const char* command) {

}



