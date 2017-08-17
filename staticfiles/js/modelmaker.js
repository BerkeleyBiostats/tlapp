var variable_names = [
	"studyid",
	"subjid",
	"siteid",
	"sex",
	"agedays",
	"WHZ",
	"region",
	"risk factor"
];

var variables = variable_names.map(function (variable_name) {
	return {
		name: variable_name,
		role: "W"
	}
});

var app = new Vue({
  delimiters: ['${', '}'],
  el: '#modelmaker',
  data: {
  	roles: ['W', 'A', 'Y'],
    message: 'Hello Vue!',
	variables: variables
  },
  computed: {

  }
});