/* =========================================================
   QuizNest — quiz-mock.js
   Drives the animated "live quiz" mockup in the hero section.
   Purely decorative / illustrative — not a real quiz engine.
   ========================================================= */
document.addEventListener("DOMContentLoaded", function () {
  var questionEl = document.getElementById("mockQuestion");
  var qNumEl = document.getElementById("mockQNum");
  var timerEl = document.getElementById("mockTimer");
  var optionsEl = document.getElementById("mockOptions");
  var progressEl = document.getElementById("mockProgress");

  if (!questionEl || !optionsEl) return;

  var questions = [
    {
      text: "A body of mass 2 kg accelerates at 5 m/s². What is the net force?",
      options: ["2 N", "5 N", "10 N", "20 N"],
      correct: 2
    },
    {
      text: "What is the SI unit of magnetic field?",
      options: ["Weber", "Tesla", "Henry", "Gauss"],
      correct: 1
    },
    {
      text: "Which functional group is present in an alcohol?",
      options: ["-COOH", "-CHO", "-OH", "-NH2"],
      correct: 2
    },
    {
      text: "What is the value of sin 30°?",
      options: ["0", "1/2", "√3/2", "1"],
      correct: 1
    },
    {
      text: "What is the derivative of x³?",
      options: ["x²", "3x", "3x²", "x³/3"],
      correct: 2
    }
  ];

  var current = 0;
  var timeLeft = 15;
  var revealed = false;
  var timerId = null;

  function renderQuestion() {
    var q = questions[current];
    revealed = false;
    timeLeft = 15;

    qNumEl.textContent = "Question " + (current + 1) + " of " + questions.length;
    timerEl.textContent = timeLeft;
    questionEl.textContent = q.text;
    progressEl.style.width = (((current) / questions.length) * 100) + "%";

    optionsEl.innerHTML = "";
    var letters = ["A", "B", "C", "D"];
    q.options.forEach(function (opt, i) {
      var li = document.createElement("li");
      li.setAttribute("data-correct", i === q.correct ? "true" : "false");
      var span = document.createElement("span");
      span.className = "qs-opt-letter";
      span.textContent = letters[i];
      li.appendChild(span);
      li.appendChild(document.createTextNode(opt));
      optionsEl.appendChild(li);
    });
  }

  function revealAnswer() {
    if (revealed) return;
    revealed = true;
    var correctLi = optionsEl.querySelector('li[data-correct="true"]');
    if (correctLi) correctLi.classList.add("is-correct");
    progressEl.style.width = (((current + 1) / questions.length) * 100) + "%";
  }

  function tick() {
    timeLeft -= 1;

    // Reveal the correct answer with a little time still on the clock,
    // mirroring "instant results" the moment an answer is confirmed.
    if (timeLeft === 8 && !revealed) {
      revealAnswer();
    }

    if (timeLeft <= 0) {
      current = (current + 1) % questions.length;
      renderQuestion();
      return;
    }

    timerEl.textContent = timeLeft;
  }

  renderQuestion();
  timerId = setInterval(tick, 900);

  // Pause the animation politely when the tab isn't visible.
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      clearInterval(timerId);
    } else {
      timerId = setInterval(tick, 900);
    }
  });
});
