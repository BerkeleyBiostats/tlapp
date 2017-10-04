Writing an analysis for tl-app
===

Input specification
---

Analyses may include user-defined inputs. Inputs are specified in a JSON field (`Fields`) in the AnalysisTemplate.

Here is an example field specification:

```
[
	{"choices": ["glmfast", "SL.glmnet"], "type": "enum", "name": "Learners"},
	{type": "float", "name": "Abar"}
]
```

After a user fills in the form, the analysis receives a JSON file like the following:

```
{
	"params": {
		"Learners": ["glmfast"],
		"Abar": 5.4
	}
}
```

Data types
---

**enum**

Generates a list of checkboxes.

```
{
	"choices": [<str>, ...], 
	"type": "enum", 
	"name": <str>
}
```

**float**

Generate a text field.

```
{
	"type": "float", 
	"name": <str>
}
```
