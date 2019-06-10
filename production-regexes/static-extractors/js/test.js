var re;

// RegExpLiteral
var _ = ''.match(/string-match/);
re = /inline-regexp-no-flags/;
re = /inline-regexp-with-flags/i;
re = /inline-regexp-with-flags/ig;

// new RegExp
var dynamicPattern = "dynamic pattern";
var dynamicFlags = "gim";

re = new RegExp("explicit-regexp-no-flags");
re = new RegExp("explicit-regexp-with-flags", "g");
re = new RegExp(dynamicPattern, "gis");
re = new RegExp("explicit-regexp-dynamic-flags", dynamicFlags);
re = new RegExp(dynamicPattern, dynamicFlags);
re = new RegExp(`explicit-regex-using-backtick-string`, "gm");

const foo = x => x, bar = x => x;

// Nesting
var baz = foo(/inline-in-func-call/g);
var result = foo(bar(new RegExp("explicit-in-func-call")));

/* Complicating the analysis. */
var j = 0;
for (var i = 0; i < 100; i++) {
    if (1) {}
      else {}
        j = 1;
}

var b = new Promise( function(resolve, reject) { process.nextTick(()=>{console.log('resolving'); resolve();}) }); 
b.then(() => {
  console.log('resolved');
  'abc'.match(re);
});

''.match('implicit regex to string match')
if (String.prototype.matchAll) ''.matchAll('implicit regex to string matchAll')
''.search('implicit regex to string search')
''.replace('not an implicit regex', "foo")
''.split('not an implicit regex')
''.split(/regex/)
''.match('dynamic regex' + ' to string match')
