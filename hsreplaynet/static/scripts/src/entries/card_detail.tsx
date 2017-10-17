import * as React from "react";
import * as ReactDOM from "react-dom";
import CardData from "../CardData";
import CardDetail from "../pages/CardDetail";
import UserData from "../UserData";
import Fragments from "../components/Fragments";
import HSReplayNetProvider from "../components/HSReplayNetProvider";

const cardId = document.getElementById("card-info").getAttribute("data-card-id");
const dbfId = +document.getElementById("card-info").getAttribute("data-dbf-id");
UserData.create();

const render = (cardData: CardData) => {
	const card = cardData && cardData.fromDbf(dbfId);
	ReactDOM.render(
		<HSReplayNetProvider>
				<Fragments
				defaults={{
					gameType: "RANKED_STANDARD",
					opponentClass: "ALL",
					rankRange: "ALL",
				}}
				immutable={!UserData.isPremium() ? ["opponentClass", "rankRange"] : null}
			>
				<CardDetail
					card={card}
					cardData={cardData}
					cardId={cardId}
					dbfId={dbfId}
				/>
			</Fragments>
		</HSReplayNetProvider>,
		document.getElementById("card-container"),
	);
};

render(null);

new CardData().load(render);
