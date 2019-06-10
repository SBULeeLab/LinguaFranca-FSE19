<?php

function test($foo)
{
	    var_dump($foo);
      if (preg_filter('#abc#', 'abc')) {}
      if (preg_filter('#abc' . 'def#', 'abc')) {}
      if (preg_grep('(abc)i', 'abc')) {}
      if (preg_match_all('(abc)igA', 'abc')) {}
      if (preg_match_all('[abc]igA', 'abc')) {}
      if (preg_match_all('{abc}igA', 'abc')) {}
      if (preg_match_all('<abc\d+e>igA', 'abc')) {}
      if (preg_match($pattern, 'abc')) {}
      if (preg_replace_callback($pattern, 'abc')) {}
      if (preg_replace($pattern, 'abc')) {}
      if (preg_split($pattern, 'abc')) {}

      # https://hotexamples.com/examples/-/-/preg_replace_callback_array/php-preg_replace_callback_array-function-examples.html
			$ourtpl = preg_replace_callback_array(array('#\\<((?:else)?if\\s+(.*?)\\s+then|else\\s*/?|/if)\\>#si' => function ($m) {
        return phptpl_if($m[1], phptpl_unescape_string($m[2]));
    }, '#\\<func (htmlspecialchars|htmlspecialchars_uni|intval|floatval|urlencode|rawurlencode|addslashes|stripslashes|trim|crc32|ltrim|rtrim|chop|md5|nl2br|sha1|strrev|strtoupper|strtolower|my_strtoupper|my_strtolower|alt_trow|get_friendly_size|filesize|strlen|my_strlen|my_wordwrap|random_str|unicode_chr|bin2hex|str_rot13|str_shuffle|strip_tags|ucfirst|ucwords|basename|dirname|unhtmlentities)\\>#i' => function ($m) {
        return '".' . $m[1] . '("';
    }, '#\\</func\\>#i' => function () {
        return '")."';
    }, '#\\<template\\s+([a-z0-9_ \\-+!(),.]+)(\\s*/)?\\>#i' => function ($m) {
        return $GLOBALS['templates']->get($m[1]);
    }, '#\\<\\?=(.*?)\\?\\>#s' => function ($m) {
        return '".strval(' . phptpl_unescape_string($m[1]) . ')."';
    }, '#\\<setvar\\s+([a-z0-9_\\-+!(),.]+)\\>(.*?)\\</setvar\\>#i' => function ($m) {
        return '".(($GLOBALS["tplvars"][\'' . $m[1] . '\'] = (' . phptpl_unescape_string($m[2]) . '))?"":"")."';
    }, '#\\<\\?(?:php|\\s).+?(\\?\\>)#s' => function ($m) {
        return phptpl_evalphp(phptpl_unescape_string($m[0]), $m[1], false);
    }), $ourtpl);
}
?>
