var variableNames = [
	"studyid",
	"subjid",
	"siteid",
	"sex",
	"agedays",
	"WHZ",
	"region",
	"risk factor"
];

var variables = variableNames.map(function (variableName) {
	return {
		name: variableName,
		role: "W"
	}
});

var modelInputs = {
	fields: [{
		name: 'ABar',
		help: 'A block of help text that explains the model input.',
		type: 'float',
	}, {
		name: 'Learners',
		type: 'enum',
		choices: ['GLM', 'Random Forest', 'Regression'],
	}],
};

var app = new Vue({
  delimiters: ['${', '}'],
  el: '#modelmaker',
  data: {
  	roles: ['W', 'A', 'Y'],
    message: 'Hello Vue!',
	variables: variables,
	modelInputs: modelInputs,
  },
});