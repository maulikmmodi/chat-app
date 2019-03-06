

//Amazon service interaction JS

function getUrlVars() {
	var vars = {};
	var parts = window.location.href.replace(/[?#&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
			vars[key] = value;
	});
	return vars;
}

var id_token = getUrlVars()["id_token"];

console.log('id_token' + id_token);

AWS.config.region = 'us-west-2';
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
	IdentityPoolId: 'us-west-2:33e11cf8-2fd1-4a74-95db-4d94decb2797',
	Logins: {
		'cognito-idp.us-west-2.amazonaws.com/us-west-2_lRDr6NoUa': id_token
	}
});

var apigClient;
AWS.config.credentials.refresh(function(){
	var accessKeyId = AWS.config.credentials.accessKeyId;
	var secretAccessKey = AWS.config.credentials.secretAccessKey;
	var sessionToken = AWS.config.credentials.sessionToken;
	AWS.config.region = 'us-west-2';
	apigClient = apigClientFactory.newClient({
		accessKey: AWS.config.credentials.accessKeyId,
		secretKey: AWS.config.credentials.secretAccessKey,
		sessionToken: AWS.config.credentials.sessionToken, // this field was missing
		region: 'us-west-2'
	});
});

var messages = [], //array that hold the record of each string in chat
  lastUserMessage = "", //keeps track of the most recent input string from the user
  botMessage = "", //var keeps track of what the chatbot is going to say
  botName = 'Chatbot', //name of the chatbot
  talking = true; //when false the speach function doesn't work

	function chatbotResponse() {
		
		// User's own message for display
		userMessage();
		
		return new Promise(function (resolve, reject) {
			talking = true;
			let params = {};
			let additionalParams = {
				headers: {
				"x-api-key" : 'AaIi7HdmvmvZEIVo2riX1FLInuOdVlF2tm9hQNL6'
				}
			};
			var body = {
			"message" : lastUserMessage
			}
			apigClient.chatbotPost(params, body, additionalParams)
			.then(function(result){
				// console.log("done");
				// console.log(result.data.body);
				
				reply = result.data.body;
			
				$("<li class='replies'><p>" + reply + "</p></li>").appendTo($('.messages ul'));
				$('.message-input input').val(null);
				$('.contact.active .preview').html('<span>You: </span>' + reply);
				$(".messages").animate({ scrollTop: $(document).height() }, "fast");
				
				resolve(result.data.body);
				botMessage = result.data.body;
			}).catch( function(result){
				// Add error callback code here.
				console.log(result);
				botMessage = "Couldn't connect"
				reject(result);
			});
		})
	}


//Js for the chat application


$(".messages").animate({ scrollTop: $(document).height() }, "fast");

$("#profile-img").click(function() {
	$("#status-options").toggleClass("active");
});

$(".expand-button").click(function() {
  $("#profile").toggleClass("expanded");
	$("#contacts").toggleClass("expanded");
});

$("#status-options ul li").click(function() {
	$("#profile-img").removeClass();
	$("#status-online").removeClass("active");
	$("#status-away").removeClass("active");
	$("#status-busy").removeClass("active");
	$("#status-offline").removeClass("active");
	$(this).addClass("active");
	
	if($("#status-online").hasClass("active")) {
		$("#profile-img").addClass("online");
	} else if ($("#status-away").hasClass("active")) {
		$("#profile-img").addClass("away");
	} else if ($("#status-busy").hasClass("active")) {
		$("#profile-img").addClass("busy");
	} else if ($("#status-offline").hasClass("active")) {
		$("#profile-img").addClass("offline");
	} else {
		$("#profile-img").removeClass();
	};
	
	$("#status-options").removeClass("active");
});

function userMessage() {

    // $.get( "https://f8laeb74pl.execute-api.us-west-2.amazonaws.com/chat-test", function( data ) {
    //     reply = data.body;
        
    //     $("<li class='replies'><p>" + reply + "</p></li>").appendTo($('.messages ul'));
    //     $('.message-input input').val(null);
    //     $('.contact.active .preview').html('<span>You: </span>' + reply);
    //     $(".messages").animate({ scrollTop: $(document).height() }, "fast");
    //   });

	message = $(".message-input input").val();
	if($.trim(message) == '') {
		return false;
	}
	$('<li class="sent"><p>' + message + '</p></li>').appendTo($('.messages ul'));
	$('.message-input input').val(null);
	$('.contact.active .preview').html('<span>You: </span>' + message);
	$(".messages").animate({ scrollTop: $(document).height() }, "fast");
};

$('.submit').click(function() {
	// newMessage();
	chatbotResponse();
});

$(window).on('keydown', function(e) {
  if (e.which == 13) {
		// newMessage();
		chatbotResponse();
    return false;
  }
});