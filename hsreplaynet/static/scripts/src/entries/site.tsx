import React from "react";
import ReactDOM from "react-dom";
import $ from "jquery";
import { cookie } from "cookie_js";
import UserData from "../UserData";
import Modal from "../components/Modal";
import CollectionSetup from "../components/collection/CollectionSetup";
import { Provider as BlizzardAccountProvider } from "../components/utils/hearthstone-account";
import AccountNavigation from "../components/account/AccountNavigation";
import PremiumModal from "../components/premium/PremiumModal";
import i18n from "../i18n";
import { I18nextProvider } from "react-i18next";
import AdUnit from "../components/ads/AdUnit";
import { SubscriptionEvents } from "../metrics/Events";

UserData.create();
const t = i18n.getFixedT(UserData.getLocale());

function renderNavbar() {
	const userNav = document.getElementById("user-nav");
	if (userNav) {
		const hideLogin = !!+userNav.getAttribute("data-hide-login");
		ReactDOM.render(
			<I18nextProvider i18n={i18n} initialLanguage={UserData.getLocale()}>
				<BlizzardAccountProvider>
					<AccountNavigation
						isAuthenticated={UserData.isAuthenticated()}
						isStaff={UserData.isStaff()}
						hideLogin={hideLogin}
						isPremium={UserData.isPremium()}
					/>
				</BlizzardAccountProvider>
			</I18nextProvider>,
			userNav,
		);
	}
}

function renderFooterAds() {
	const containers = document.getElementsByClassName("footer-ad-container");
	for (let i = 0; i < containers.length; i++) {
		ReactDOM.render(
			<AdUnit id={`ft-d-${i + 1}`} size="320x50" />,
			containers.item(i),
		);
	}
}

function trackPurchase() {
	const justSubscribed = cookie.get("just-subscribed");
	if (justSubscribed) {
		if (UserData.isPremium()) {
			const { value, label } = JSON.parse(justSubscribed);
			SubscriptionEvents.onSubscribe(value, label);
		}
		cookie.removeSpecific("just-subscribed", { path: "/" });
	}
}

if (document.readyState === "loading") {
	document.addEventListener("DOMContentLoaded", renderNavbar);
	document.addEventListener("DOMContentLoaded", renderFooterAds);
} else {
	renderNavbar();
	renderFooterAds();
}

if (window) {
	const waitForFbq = window.setInterval(() => {
		if (typeof fbq !== "function") {
			return;
		}
		trackPurchase();
		window.clearInterval(waitForFbq);
	}, 1000);
}

function checkModal() {
	if (!document || !document.location || !document.location.search) {
		return;
	}
	const search = document.location.search.replace(/^\?/, "");
	const parts = search.split("&");
	for (const part of parts) {
		let param = part.split("=", 2);
		if (param[0] === "premium-modal") {
			// url compat
			param = ["modal", "premium"];
		}
		if (param.length !== 2) {
			continue;
		}
		const [key, value] = param;
		if (key === "modal") {
			const modalDummy = document.createElement("div");
			modalDummy.setAttribute("id", "initial-modal-dummy");
			switch (value) {
				case "collection":
					ReactDOM.render(
						<I18nextProvider
							i18n={i18n}
							initialLanguage={UserData.getLocale()}
						>
							<BlizzardAccountProvider>
								<Modal
									visible
									onClose={() => {
										ReactDOM.unmountComponentAtNode(
											modalDummy,
										);
									}}
								>
									<CollectionSetup />
								</Modal>
							</BlizzardAccountProvider>
						</I18nextProvider>,
						modalDummy,
					);
					break;
				case "premium":
					ReactDOM.render(
						<I18nextProvider
							i18n={i18n}
							initialLanguage={UserData.getLocale()}
						>
							<Modal
								visible
								onClose={() => {
									ReactDOM.unmountComponentAtNode(modalDummy);
								}}
							>
								<PremiumModal
									analyticsLabel={"URL Parameter"}
									modalStyle="default"
								/>
							</Modal>
						</I18nextProvider>,
						modalDummy,
					);
					break;
			}
			document.body.appendChild(modalDummy);
			break;
		}
	}
}

if (document && document.body) {
	checkModal();
} else {
	document.addEventListener("DOMContentLoaded", () => {
		checkModal();
	});
}

function showPopover(
	targetElementId,
	requiredFeature,
	requiresAuthentication,
	cookieKey,
	title,
	content,
	options = null,
) {
	const element = document.getElementById(targetElementId);
	if (!element) {
		return;
	}

	if (requiredFeature && !UserData.hasFeature(requiredFeature)) {
		return;
	}

	if (requiresAuthentication && !UserData.isAuthenticated()) {
		return;
	}

	if (cookie.get(cookieKey, "0") !== "0") {
		return;
	}

	const defaultOptions = {
		animation: true,
		trigger: "manual",
		placement: "bottom",
		html: true,
	};

	if (options) {
		Object.assign(defaultOptions, options);
	}

	const closeId = targetElementId + "-popover-close";
	const closeBtn = `<a href="#" id="${closeId}" class="popover-close" aria-hidden="true">&times;</a>`;

	Object.assign(defaultOptions, {
		title: `${title} ${closeBtn}`,
		content,
	});

	$(element).popover(defaultOptions);
	$(element).on("shown.bs.popover", () => {
		$("#" + closeId).click(evt => {
			evt.preventDefault();
			$(element).popover("destroy");
			cookie.set(cookieKey, "1", {
				path: "/",
				expires: 90,
			});
		});
	});
	setTimeout(() => ($(element) as any).popover("show"), 500);
}

if (
	window &&
	window.location &&
	window.location.pathname.match(/\/(replay|games|decks|cards)\//)
) {
	document.addEventListener("DOMContentLoaded", () => {
		showPopover(
			"navbar-link-premium",
			"reflinks",
			true,
			"refer-popup-closed",
			t("Refer a Friend!"),
			t(
				"Tell a friend about HSReplay.net for a cheaper Premium subscription!",
			),
		);

		if (["th"].indexOf(UserData.getLocale()) !== -1) {
			showPopover(
				"navbar-language-selector",
				"translation-popover",
				false,
				"translation-popup-closed",
				t("Help translate HSReplay.net"),
				t(
					"Want to see more of HSReplay.net in your native language? Click here to see how you can help translate the site…",
				),
			);
		}

		if (
			window.location.pathname.indexOf("/decks/") !== -1 &&
			window.innerWidth > 768
		) {
			showPopover(
				"high-legend-filter",
				"high-legend-filter-promo",
				false,
				"high-legend-filter-popup-closed",
				t("New Top Legend Filter!"),
				t(
					"Want to see what decks all the pros are winning with? Find out right here!",
				),
				{ placement: "right", container: "body" },
			);
		}
	});
}
