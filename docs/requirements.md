# Requirements

## US-01 Shorten URL
As a user I want to shorten a long link so that I can share it easily.
- Given a valid http(s) URL, it returns a 6-character code
- The same URL returns the same code
- An invalid URL raises ValueError

## US-02 Resolve code
As a user I want to get the original URL so that I can visit the target.
- An existing code returns the original URL
- A non-existent code raises KeyError

## US-03 Count visits
As a link owner I want to see the visits so that I can measure reach.
- Each resolution increments the counter by 1
