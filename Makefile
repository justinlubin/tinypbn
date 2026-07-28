README.html: README.md basic.css
	pandoc --from markdown+tex_math_dollars --mathml --standalone --css basic.css -o README.html README.md
