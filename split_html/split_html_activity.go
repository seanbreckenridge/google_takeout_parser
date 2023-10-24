package main

import (
	"bytes"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/net/html"
)

type Flags struct {
	input     string
	cellCount int
	outputDir string
}

func parseFlags() (*Flags, error) {
	var input string
	var outputDir string
	var cellCount int
	flag.IntVar(&cellCount, "count", 1000, "how many cells to split into each file")
	flag.StringVar(&outputDir, "output", "", "output directory. if not specified, will use the directory of the input file")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [options] input\n", os.Args[0])
		flag.PrintDefaults()
	}
	flag.Parse()
	if flag.NArg() == 0 {
		flag.Usage()
		fmt.Printf("an input file is required\n")
		os.Exit(1)
	}
	input = flag.Arg(0)

	info, err := os.Stat(input)
	if os.IsNotExist(err) {
		return nil, fmt.Errorf("input file '%s' does not exist", input)
	}

	if info.IsDir() {
		return nil, fmt.Errorf("input file '%s' is a directory", input)
	}

	absPath, err := filepath.Abs(input)
	if err != nil {
		return nil, err
	}

	if outputDir == "" {
		outputDir = filepath.Dir(absPath)
	}

	if cellCount < 1 {
		return nil, fmt.Errorf("cell count must be greater than 0")
	}

	return &Flags{input: input, cellCount: cellCount, outputDir: outputDir}, nil
}

// Function to check if a token has a specific class
func hasClass(token html.Token, class string) bool {
	for _, attr := range token.Attr {
		if attr.Key == "class" && strings.Contains(attr.Val, class) {
			return true
		}
	}
	return false
}

func readAndWriteToPartials(flags *Flags) error {
	input, err := os.Open(flags.input)
	if err != nil {
		return err
	}
	defer input.Close()

	var outputFile *os.File
	var outputFileName string
	currentFile := 1

	openOutputFile := func() error {
		// if we have an open file, close it and increment the current file
		if outputFile != nil {
			outputFile.Close()
			currentFile++
		}
		outputFileName = filepath.Join(flags.outputDir, fmt.Sprintf("MyActivity-%04d.html", currentFile))
		var err error
		outputFile, err = os.Create(outputFileName)
		if err != nil {
			return err
		}
		return nil
	}

	err = openOutputFile()
	if err != nil {
		return err
	}
	defer outputFile.Close()

	writtenCount := 0

	writeBuffer := func(data []byte) error {
		// if we've written enough, close the file and open a new one
		if writtenCount >= flags.cellCount {
			ferr := openOutputFile()
			if ferr != nil {
				return ferr
			}
			writtenCount = 0
			if outputFile == nil {
				return fmt.Errorf("output file is not open")
			}
		}
		// note: panics if outputFile is nil, but that should never happen
		_, err := outputFile.Write(data)
		return err
	}

	z := html.NewTokenizer(input)
	// find the div.outer-cell and 'start' a block there,
	// copying all tokens till we end that block
	// need to keep track of divDepth, so we know when we're done
	divDepth := 0
	inBlock := false
	var blockContent bytes.Buffer

	blockContent = bytes.Buffer{}

	for {
		tt := z.Next()
		switch tt {
		case html.ErrorToken:
			if z.Err() == io.EOF {
				// done, defers should cleanup the rest
				if len(blockContent.String()) > 0 {
					return fmt.Errorf("found EOF, but block content is not empty")
				}
				return nil
			} else {
				return z.Err()
			}
		case html.DoctypeToken, html.CommentToken:
			// skip these
		case html.StartTagToken:
			t := z.Token()
			if t.Data == "div" && hasClass(t, "outer-cell") {
				if inBlock {
					return fmt.Errorf("found start tag for outer-cell, but we're already in a block")
				}
				inBlock = true
			}
			// if were in the block, write any start tags to the block content
			if inBlock {
				blockContent.Write(z.Raw())
				if t.Data == "div" {
					divDepth++
				}
			}

		case html.EndTagToken:
			t := z.Token()
			// if we're ending a tag for outer-cell, we would be here at depth 1
			// this means we're done with the block
			if inBlock && divDepth == 1 {
				// we're done with the block, write it out
				// and reset the block content

				// add the end tag to the block content
				blockContent.Write(z.Raw())
				blockContent.Write([]byte("\n"))

				// write to file
				writeBuffer(blockContent.Bytes())
				writtenCount++

				// reset the block content
				blockContent.Reset()
				inBlock = false
				divDepth = 0
			}

			// otherwise, if we're in a block, add the end tag to the block content
			if inBlock {
				if t.Data == "div" {
					divDepth--
				}
				blockContent.Write(z.Raw())
			}

		case html.SelfClosingTagToken, html.TextToken:
			// if we're in a block, add data to the buffer
			if inBlock {
				blockContent.Write(z.Raw())
			}
		default:
			return fmt.Errorf("unknown token type: %v", tt)
		}
	}
}

func splitHtmlActivity() error {
	flags, err := parseFlags()
	if err != nil {
		return err
	}

	rerr := readAndWriteToPartials(flags)
	if rerr != nil {
		return rerr
	}

	return nil
}

func main() {
	err := splitHtmlActivity()
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
