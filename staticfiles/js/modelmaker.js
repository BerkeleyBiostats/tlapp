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
		value: null,
	}, {
		name: 'Learners',
		type: 'enum',
		choices: ['GLM', 'Random Forest', 'Regression'],
		value: [],
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
  methods: {
  	sendJob: function (event) {
  		var parameters = this.modelInputs.fields.map(function (field) {
  			return {
  				name: field.name,
  				value: field.value,
  			};
  		});
  		console.log(parameters);
  	},
  },
});



