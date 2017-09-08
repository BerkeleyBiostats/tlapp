G.datasets = G.datasets.map(function (dataset) {
	dataset.variables = dataset.variables.map(function (variableName) {
		return {
			name: variableName,
			role: "W",
		};
	});
	return dataset;
});

var app = new Vue({
  delimiters: ['${', '}'],
  el: '#modelmaker',
  data: {
  	roles: ['W', 'A', 'Y'],
    message: 'Hello Vue!',
	modelTemplates: G.models,
	selectedTemplate: G.models[0],
	datasets: G.datasets,
	activeDataset: G.datasets[0],
  },
  methods: {
  	sendJob: function (event) {
  		var inputs = {};
  		inputs.fields = this.selectedTemplate.fields.map(function (field) {
  			return {
  				name: field.name,
  				value: field.value,
  			};
  		});

  		var whereRole = (variables, role) => {
  			return variables.filter(function (variable) {
  				return variable.role === role;
  			});
  		};

  		var whereRoleForActive = (role) => {
  			var vars = whereRole(this.activeDataset.variables, role);
  			return vars.map(function (variable) {
  				return variable.name;
  			});
  		};

  		inputs.data = {
  			uri: this.activeDataset.url,
  			type: 'csv',
  			nodes: {
  				Y: whereRoleForActive('Y'),
  				A: whereRoleForActive('A'),
  				W: whereRoleForActive('W'),
  			}
  		};

  		console.log(inputs);

  		var job = {
  			inputs,
  			model_template: this.selectedTemplate.id,
  		};

  		// GET /someUrl
		this.$http.post('/submit_job/', job).then(response => {
			console.log(response.data);
			// window.location.href = '/jobs/';
		}, response => {
		});
  	},
  },
});



