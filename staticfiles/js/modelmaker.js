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

G.datasets = G.datasets.map(function (dataset) {
	dataset.variables = dataset.variables.map(function (variableName) {
		return {
			name: variableName,
			role: "W",
		};
	});
	return dataset;
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
	}, {
		name: 'Spacing',
		type: 'enum',
		choices: ['tight', 'loose'],
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
	modelTemplates: G.models,
	selectedTemplate: G.models[0],
	datasets: G.datasets,
	activeDataset: G.datasets[0],
  },
  methods: {
  	sendJob: function (event) {
  		var parameters = this.modelInputs.fields.map(function (field) {
  			return {
  				name: field.name,
  				value: field.value,
  			};
  		});

  		var job = {
  			parameters,
  			model_template: this.selectedTemplate.id,
  		};

  		// GET /someUrl
		this.$http.post('/submit_job/', job).then(response => {
			console.log(response.data);
			window.location.href = '/jobs/';
		}, response => {
		});
  	},
  },
});



