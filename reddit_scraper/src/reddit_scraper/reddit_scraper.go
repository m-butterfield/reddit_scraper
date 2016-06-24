package main

import (
	"fmt"

	"github.com/docopt/docopt-go"
)

func main() {
	usage := `
reddit_scraper

Scrape images from a subreddit.

Usage:
  reddit_scraper initialize
  reddit_scraper backfill <subreddit> <date>
  reddit_scraper scrape <subreddit>

Options:
  -h --help              Show this screen
`
	arguments, _ := docopt.Parse(usage, nil, true, "", false)
	fmt.Println(arguments)
}
